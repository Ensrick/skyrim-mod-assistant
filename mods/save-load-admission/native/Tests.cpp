// SPDX-License-Identifier: MIT
// Synthetic redistributable fixtures; no player saves or third-party assets.
#include "SaveAdmission.h"
#include <iostream>
#include <functional>
#include <zlib.h>
using namespace Ensrick::SaveAdmission;
using Buffer = std::vector<std::uint8_t>;
static unsigned checks;
static void Check(bool v) { ++checks; if (!v) throw std::runtime_error("test assertion failed"); }
template<class T> void Num(Buffer& b, T v) {
    for (unsigned i=0; i<sizeof(T); ++i) b.push_back(std::uint64_t(v) >> (i*8));
}
static void Text(Buffer& b, std::string_view text) { b.insert(b.end(), text.begin(), text.end()); }
static void Str(Buffer& b, const std::string& text) { Num<std::uint16_t>(b, text.size()); Text(b, text); }
static void Add(Buffer& b, const Buffer& other) { b.insert(b.end(), other.begin(), other.end()); }
static std::uint32_t U32(const Buffer& b, std::size_t offset) {
    std::uint32_t value=0;
    for (unsigned i=0;i<4;++i) value|=std::uint32_t(b.at(offset+i))<<(i*8);
    return value;
}
static void Put32(Buffer& b, std::size_t offset, std::uint32_t value) {
    for (unsigned i=0;i<4;++i) b.at(offset+i)=value>>(i*8);
}
static void Refused(const std::function<void()>& action) {
    try { action(); } catch (const InvalidInput&) { ++checks; return; }
    throw std::runtime_error("malformed fixture accepted");
}
static Buffer Table(const PluginTable& t) {
    Buffer b; Num<std::uint8_t>(b, t.full.size());
    for (const auto& n:t.full) Str(b,n);
    Num<std::uint16_t>(b,t.light.size());
    for (const auto& n:t.light) Str(b,n);
    return b;
}
static Buffer Literal(const Buffer& b) {
    Buffer out;
    if (b.size()<15) out.push_back(b.size()<<4);
    else {
        out.push_back(0xF0);
        auto remaining=b.size()-15;
        while (remaining>=255) {out.push_back(255); remaining-=255;}
        out.push_back(remaining);
    }
    Add(out,b); return out;
}
static Buffer Body(const PluginTable& t) {
    const auto table=Table(t);
    Buffer b{78}; Num<std::uint32_t>(b,table.size()); Add(b,table); return b;
}
static Buffer Save(std::uint16_t compression, const Buffer& body, const Buffer* packedOverride=nullptr,
    std::uint32_t width=1, std::uint32_t height=1) {
    Buffer h; Num<std::uint32_t>(h,12); Num<std::uint32_t>(h,7); Str(h,"Test");
    Num<std::uint32_t>(h,3); Str(h,"Winterhold"); Str(h,"000.00.09"); Str(h,"NordRace");
    h.insert(h.end(),18,0); Num(h,width); Num(h,height); Num(h,compression);
    Buffer out; Text(out,"TESV_SAVEGAME"); Num<std::uint32_t>(out,h.size()); Add(out,h);
    out.insert(out.end(),4,0);
    if (!compression) Add(out,body);
    else {
        Buffer packed;
        if (packedOverride) packed=*packedOverride;
        else if (compression==1) {
            uLongf size=compressBound(body.size()); packed.resize(size);
            Check(compress2(packed.data(),&size,body.data(),body.size(),9)==Z_OK); packed.resize(size);
        } else packed=Literal(body);
        Num<std::uint32_t>(out,body.size()); Num<std::uint32_t>(out,packed.size()); Add(out,packed);
    }
    return out;
}
static Buffer Record(std::uint64_t fingerprint=123, std::uint64_t value=23,
    std::uint64_t backend=23, std::uint64_t physical=23, std::uint32_t version=2) {
    Buffer out; Text(out,"ECMK"); Num(out,version); Num<std::uint32_t>(out,40);
    Text(out,"ECV2"); Num<std::uint32_t>(out,2);
    Num(out,fingerprint); Num(out,value); Num(out,backend); Num(out,physical); return out;
}
static Buffer Plugin(const std::vector<Buffer>& chunks, const std::string& id="ECDN") {
    Buffer body; for (const auto& c:chunks) Add(body,c);
    Buffer out; Text(out,id); Num<std::uint32_t>(out,chunks.size()); Num<std::uint32_t>(out,body.size()); Add(out,body); return out;
}
static Buffer CoSave(const std::vector<Buffer>& plugins) {
    Buffer out; Text(out,"SKSE"); Num<std::uint32_t>(out,1); Num<std::uint32_t>(out,0);
    Num<std::uint32_t>(out,0); Num<std::uint32_t>(out,plugins.size());
    for (const auto& p:plugins) Add(out,p); return out;
}
int main() {
    try {
        const PluginTable table{{"Skyrim.esm","Example.esp"},{"TrueHUD.esl"}};
        const auto body=Body(table);
        for (unsigned c=0;c<3;++c) {
            const auto raw=Save(c,body);
            const auto info=ParseESS(raw);
            Check(info.number==7&&info.level==3&&info.compression==c&&info.formVersion==78);
            Check(info.plugins.full==table.full&&info.plugins.light==table.light);
            for (std::size_t n=0;n<raw.size();++n) Refused([&]{ParseESS(Bytes(raw).first(n));});
            if (c) {auto extra=raw; extra.push_back(0); Refused([&]{ParseESS(extra);});}
        }
        Check(ComparePlugins(table,table).empty());
        Check(ComparePlugins(table,{{"sKYRIM.esm","example.ESP","Extra.esp"},{"trueHUD.ESL"}}).empty());
        const auto changed=ComparePlugins(table,{{"Skyrim.esm","TrueHUD.esl"},{"Example.esp"}});
        Check(changed.size()==2&&changed[0].starts_with("plugin type changed:"));
        Check(ComparePlugins(table,{{"Skyrim.esm"},{}}).size()==2);
        for (const auto& bad:std::vector<PluginTable>{
            {{},{}},{{"Skyrim.esm"},{"SKYRIM.ESM"}},{{"../Skyrim.esm"},{}},
            {{"Skyrim.exe"},{}},{{std::string("A\0.esp",6)},{}},{{"A\n.esp"},{}},
            {{"C:bad.esp"},{}},{{""},{}},{{".esp"},{}},
            {{"\xC0\xAF" "bad.esp"},{}},{{"\xED\xA0\x80" ".esp"},{}},
            {{"\xF4\x90\x80\x80" ".esp"},{}},{{"\xE2" ".esp"},{}}}) {
            Refused([&]{ParseESS(Save(0,Body(bad)));});
            Refused([&]{ComparePlugins(table,bad);});
        }
        const PluginTable utf8{{"Skyrim.esm","\xC3\xA9" ".esp"},{}};
        Check(ComparePlugins(ParseESS(Save(1,Body(utf8))).plugins,utf8).empty());
        Refused([&]{ParseESS(Save(3,body));});
        Refused([&]{ParseESS(Save(0,body,nullptr,0xFFFFFFFF,0xFFFFFFFF));});
        auto old=body;old[0]=77;Refused([&]{ParseESS(Save(0,old));});
        auto extraTable=body;extraTable[1]++;extraTable.push_back(0);Refused([&]{ParseESS(Save(0,extraTable));});
        for (const Buffer& malformed:std::vector<Buffer>{{0},{0xF0},{0,0,0},{0x10,'a',0,0},{0x10,'a',2,0},{0xF0,255,255}})
            Refused([&]{ParseESS(Save(2,body,&malformed));});
        auto z=Save(1,body); z.back()^=0xFF;Refused([&]{ParseESS(z);});
        for (unsigned compression:{1u,2u}) {
            auto encoded=Save(compression,body);
            const auto sizeOffset=17+U32(encoded,13)+4;
            for (auto declared:{0u,1u,std::uint32_t(body.size()-1),std::uint32_t(body.size()+1),0xFFFFFFFFu}) {
                auto bad=encoded;Put32(bad,sizeOffset,declared);Refused([&]{ParseESS(bad);});
            }
            if(compression==1) {
                // A complete deflate stream with extra bytes INSIDE packedSize.
                encoded.push_back(0);Put32(encoded,sizeOffset+4,U32(encoded,sizeOffset+4)+1);
                Refused([&]{ParseESS(encoded);});
            }
        }
        // Overlapping LZ4 matches in ignored world bytes still exercise decoding.
        auto packed=Literal(body); packed[0]|=5;packed.push_back(1);packed.push_back(0);
        // Match repeats the last byte of the plugin name; use the actual byte.
        auto overlapping=body;overlapping.insert(overlapping.end(),9,body.back());
        Check(ParseESS(Save(2,overlapping,&packed)).plugins.full==table.full);
        const auto co=CoSave({Plugin({Record()})});
        const auto checkpoint=ParseCurrencyCheckpoint(co,123);
        Check(checkpoint.value==23&&checkpoint.backend==23&&checkpoint.physical==23&&checkpoint.fingerprint==123);
        for (std::size_t n=0;n<co.size();++n) Refused([&]{ParseCurrencyCheckpoint(Bytes(co).first(n),123);});
        for (const Buffer& bad:std::vector<Buffer>{CoSave({}),CoSave({Plugin({})}),
            CoSave({Plugin({Record(),Record()})}),CoSave({Plugin({Record()}),Plugin({Record()})}),
            CoSave({Plugin({Record(124)})}),CoSave({Plugin({Record(123,0x80000000)})}),
            CoSave({Plugin({Record(123,1,0x80000000)})}),CoSave({Plugin({Record(123,1,1,0x80000000)})}),
            CoSave({Plugin({Record(123,1,1,1,1)})}),CoSave({Plugin({Record(123,1,1,1,3)})})})
            Refused([&]{ParseCurrencyCheckpoint(bad,123);});
        auto trailing=co;trailing.push_back(0);Refused([&]{ParseCurrencyCheckpoint(trailing,123);});
        Refused([&]{ParseCurrencyCheckpoint(co,0);});
        Check(ParseCurrencyCheckpoint(CoSave({Plugin({Record()},"OTHR"),Plugin({Record(123,0,100,0)})}),123).backend==100);
        Check(ParseCurrencyCheckpoint(CoSave({Plugin({Record(123,0x7FFFFFFF,0x7FFFFFFF,0x7FFFFFFF)})}),123).value==0x7FFFFFFF);
        std::cout<<checks<<" native parser/policy checks passed\n";
    } catch (const std::exception& e) {std::cerr<<"after "<<checks<<" checks: "<<e.what()<<'\n';return 1;}
}
