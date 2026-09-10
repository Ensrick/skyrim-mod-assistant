"""Generate a separate, pinned Unbound source patch; never edit vendor inputs.

Original Skyrim Unbound Reborn: chinagreenelvis / lilebonymace, Nexus27962.
Bug-fix redistribution permitted with credit (permissions checked 2026-09-09).
This generator includes only the small replacement fragment, not vendor assets.
Generated source/PEX remains a derivative with the author's permissions.
"""
import argparse
import hashlib
from pathlib import Path

SOURCE_SHA256 = '6e4e9fd57f355525740b15673b1d06b2ef2257703cd23f29534cbc01ea575b2a'
OLD = ('\t\t\tSuitableLocations.AddForms(suitableHoldsArray)\n'
       '\t\t\tSuitableLocationsConditionless.AddForms(suitableHoldsArray)')
NEW = '''\t\t\t; Ensrick #263: only jail-capable holds are jail destinations.
\t\t\t; Other/non-jail holds remain eligible for ordinary location starts.
\t\t\tint jailCandidateIndex = 0
\t\t\twhile jailCandidateIndex < suitableHoldsArray.Length
\t\t\t\tForm jailCandidate = suitableHoldsArray[jailCandidateIndex]
\t\t\t\tif jailCandidate && HoldsWithJail.HasForm(jailCandidate)
\t\t\t\t\tSuitableLocations.AddForm(jailCandidate)
\t\t\t\t\tSuitableLocationsConditionless.AddForm(jailCandidate)
\t\t\t\telse
\t\t\t\t\tDebug.Trace("[EnsrickUnbound263] excluded non-jail hold from jail pool: " + jailCandidate)
\t\t\t\tendif
\t\t\t\tjailCandidateIndex += 1
\t\t\tendwhile'''
TRACE_ANCHOR = '\tFormList holdList\n\tif HoldsWithJail.HasForm(locationForm)'
TRACE = ('\tDebug.Trace("[EnsrickUnbound263] selected=" + locationForm + ", typeChoice=" + location1 + ", locationChoice=" + location2)\n'
         + TRACE_ANCHOR)


def transform(raw):
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('Unreviewed source hash; no output written')
    source = raw.decode('utf-8-sig').replace('\r\n', '\n')
    if source.count(OLD) != 1 or source.count(TRACE_ANCHOR) != 1:
        raise ValueError('Patch anchors are not unique; no output written')
    return source.replace(OLD, NEW).replace(TRACE_ANCHOR, TRACE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Output must be a separate file, never the vendor source')
    result = transform(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects previous test evidence too.
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(result)
    print('Prepared pinned separate source: ' + str(args.output))


if __name__ == '__main__':
    main()
