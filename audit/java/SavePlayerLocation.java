// SPDX-License-Identifier: MIT
// Original read-only consumer of pinned Apache-2.0 FallrimTools. No save writer.
import java.nio.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import resaver.ProgressModel;
import resaver.ess.*;

public final class SavePlayerLocation {
    static String hash(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    static String value(GeneralElement data, String key) {
        if (!data.hasVal(key)) return "<absent>";
        Object v = data.getVal(key);
        return v instanceof float[] f ? Arrays.toString(f) : String.valueOf(v);
    }
    public static void main(String[] args) throws Exception {
        boolean prefixOnly = args.length == 3 && args[2].equals("--prefix-only");
        if (!Boolean.getBoolean("java.awt.headless") || !(args.length == 2 || prefixOnly))
            throw new IllegalArgumentException("Requires headless=true and save.ess expectedSHA256 [--prefix-only]");
        Path path = Path.of(args[0]).toRealPath();
        if (Files.size(path) > 256L*1024*1024) throw new IllegalArgumentException("ESS exceeds limit");
        String before = hash(path);
        if (!before.equalsIgnoreCase(args[1])) throw new IllegalArgumentException("Unexpected input hash");
        System.out.println("inputSHA256=" + before);
        ESS save = ESS.readESS(path, new ModelBuilder(new ProgressModel())).ESS;
        if (save.isBroken() || save.isTruncated() || save.isPluginOverflow())
            throw new IllegalStateException("Incomplete parser result; no conclusions permitted");
        System.out.println("headerLocation=" + save.getHeader().LOCATION);
        int matches = 0;
        boolean positionPresent = false;
        for (ChangeForm cf : save.getChangeForms()) {
            if (cf.getRefID() == null || !cf.getRefID().equals(0x14)) continue;
            ++matches;
            System.out.printf("playerRef=%s type=%s flags=%s%n", cf.getRefID().toHex(), cf.getType(), cf.getChangeFlags());
            if (cf.getType() != ChangeForm.Type.ACHR) throw new IllegalStateException("Player is not ACHR");
            // Reject partial/best-effort bodies for this independent cross-check.
            ChangeFormData body = cf.getData(Optional.empty(), save.getContext(), false);
            if (!(body instanceof ChangeFormACHR) || ((ChangeFormACHR)body).hasUnparsed()) {
                if (!prefixOnly) throw new IllegalStateException("ACHR body incomplete; no position certificate");
                System.out.println("fullAchrParsed=false; explicitly inspecting INITIAL prefix only");
                // This is a bounded prefix format, independently of the unparsed
                // trailing body. Definitions: pinned ChangeFormACHR/InitialData.
                var flags = cf.getChangeFlags();
                int type = flags.getFlag(ChangeFlagConstantsAchr.CHANGE_REFR_PROMOTED)
                    || flags.getFlag(ChangeFlagConstantsAchr.CHANGE_REFR_CELL_CHANGED) ? 6
                    : flags.getFlag(ChangeFlagConstantsAchr.CHANGE_REFR_HAVOK_MOVE)
                    || flags.getFlag(ChangeFlagConstantsAchr.CHANGE_REFR_MOVE) ? 4 : 0;
                if (type == 0) { System.out.println("INITIAL=<absent>"); continue; }
                ByteBuffer raw = cf.getBodyData();
                int size = type == 6 ? 34 : 27;
                if (raw == null || raw.remaining() < size) throw new IllegalStateException("Truncated INITIAL prefix");
                raw = raw.slice().order(ByteOrder.LITTLE_ENDIAN);
                raw.limit(size);
                RefID cell = save.getContext().readRefID(raw);
                float[] pos = new float[3], rot = new float[3];
                for (int i=0;i<3;i++) pos[i] = raw.getFloat();
                for (int i=0;i<3;i++) rot[i] = raw.getFloat();
                for (float v : pos) if (!Float.isFinite(v)) throw new IllegalStateException("Nonfinite position");
                for (float v : rot) if (!Float.isFinite(v)) throw new IllegalStateException("Nonfinite rotation");
                String starting = "<absent>";
                if (type == 6) { starting = save.getContext().readRefID(raw).toHex(); raw.getShort(); raw.getShort(); }
                if (raw.hasRemaining()) throw new IllegalStateException("Prefix size mismatch");
                System.out.printf("prefixType=%d prefixBytes=%d CELL=%s POS=%s ROT=%s STARTING_CELL=%s%n",
                    type, size, cell.toHex(), Arrays.toString(pos), Arrays.toString(rot), starting);
                positionPresent = true;
                continue;
            }
            ChangeFormACHR actor = (ChangeFormACHR) body;
            GeneralElement initial = actor.getGeneralElement("INITIAL");
            if (initial == null) {
                System.out.println("INITIAL=<absent>");
                continue;
            }
            System.out.printf("INITIAL CELL=%s POS=%s ROT=%s STARTING_CELL=%s%n",
                value(initial, "CELL"), value(initial, "POS"), value(initial, "ROT"), value(initial, "STARTING CELL"));
            positionPresent = initial.hasVal("POS");
        }
        if (matches != 1) throw new IllegalStateException("Player match count must be exactly one: " + matches);
        // Preserve opaque global data as bounded raw evidence, not an invented
        // position/worldspace decode from an unverified format description.
        for (GlobalData g : save.getTable1()) if (g.getType() == 2) {
            if (g.getDataBlock() instanceof DefaultGlobalDataBlock block) {
                ByteBuffer raw = block.getData().duplicate();
                raw.rewind();
                int length = raw.remaining();
                byte[] prefix = new byte[Math.min(length, 64)];
                raw.get(prefix);
                System.out.printf("globalData2 opaqueBytes=%d prefixHex=%s%n", length, HexFormat.of().formatHex(prefix));
            }
        }
        if (!before.equals(hash(path))) throw new IllegalStateException("Input changed during inspection");
        System.out.println("inspectionFinished=true inputUnchanged=true serializedPositionPresent=" + positionPresent);
        System.out.println("scope=Serialized INITIAL only; prefixOnlyMode=" + prefixOnly + "; not full ACHR validation, overall save health or runtime compatibility");
    }
}
