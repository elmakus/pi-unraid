#!/usr/bin/env python3
"""Coordinated latest-stable update-resolution entrypoint (M05-T01).

Resolves every approved versioned global component together from its accepted
stable line, freezes one exact immutable candidate, and stages it for the
later build path. Resolution only stages a candidate: it never reconciles
current desired state, never runs doctor checks, never builds images, and
never promotes/cuts over production. Default output is read-only stdout;
--output stages to a separate path and can never overwrite the accepted
candidate. A compatibility lag is applied only with an approved exception
bound to a verifiable durable authority record; anything else fails closed.
"""
from __future__ import annotations

import argparse, copy, hashlib, json, os, re, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path

SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA256=re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER=re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
UA="pi-unraid-paseo-candidate-resolver/1"
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY=ROOT/"config"/"environment-capabilities.json"

REQUIRED_COMPONENTS={"paseo","node","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"}
EXPECTED_SOURCE_REPO={"paseo":"getpaseo/paseo","pi":"earendil-works/pi","playwright":"microsoft/playwright",
    "specpi":"tannermidd/SpecPi","pi_mcp_adapter":"nicobailon/pi-mcp-adapter","github_cli":"cli/cli",
    "docker_cli":"docker/cli","docker_compose":"docker/compose"}
EXPECTED_NPM_PACKAGE={"pi":"@earendil-works/pi-coding-agent","playwright":"playwright","specpi":"specpi","pi_mcp_adapter":"pi-mcp-adapter"}
BINARY_PATTERNS={"github_cli":r"gh_{version}_linux_amd64\.tar\.gz","docker_compose":r"docker-compose-linux-x86_64"}
GENERIC_BASE_TOOLING=["bash","git","network-tools","build-tools","python3"]
GENERIC_BASE_TOOLING_IDENTITY="owned by the exact Paseo child-image package graph; not independent floating version lines"
NODE_FLOOR=(22,19,0)
CHANNEL_MARKERS=("latest","nightly","beta","alpha","rc","canary","next","edge","snapshot","master","main")

STABLE_LINES={
 "paseo":{"channel":"latest-stable","source":"github-releases-latest:getpaseo/paseo + ghcr:getpaseo/paseo immutable digest",
   "rationale":"Accepted line is the latest non-prerelease GitHub release; the GHCR tag must resolve to one immutable digest with a unique linux/amd64 manifest."},
 "node":{"channel":"derived","source":"paseo-image-NODE_VERSION",
   "rationale":"Node is not an independent floating line; it is inherited from the exact immutable Paseo parent image and must satisfy the Pi floor >=22.19.0."},
 "pi":{"channel":"latest-stable","source":"npm-latest:@earendil-works/pi-coding-agent + github-releases-latest:earendil-works/pi (must agree)",
   "rationale":"Accepted line is npm latest agreeing with the latest non-prerelease GitHub release; prerelease versions are rejected."},
 "playwright":{"channel":"latest-stable","source":"npm-latest:playwright + github-releases-latest:microsoft/playwright (must agree); chromium derived from browsers.json",
   "rationale":"Accepted line is npm latest agreeing with the latest non-prerelease GitHub release; Chromium identity is derived from that exact release."},
 "specpi":{"channel":"latest-stable","source":"npm-latest:specpi + github-releases-latest:tannermidd/SpecPi (must agree)",
   "rationale":"Accepted line is npm latest agreeing with the latest non-prerelease GitHub release; prerelease versions are rejected."},
 "pi_mcp_adapter":{"channel":"latest-stable","source":"npm-latest:pi-mcp-adapter + github-releases-latest:nicobailon/pi-mcp-adapter (must agree)",
   "rationale":"Accepted line is npm latest agreeing with the latest non-prerelease GitHub release; the declared Pi-AI peer range must cover the resolved Pi minor."},
 "github_cli":{"channel":"latest-stable","source":"github-releases-latest:cli/cli + release asset digest",
   "rationale":"Accepted line is the latest non-prerelease GitHub release with its pinned release-asset digest."},
 "docker_cli":{"channel":"latest-stable","source":"github-releases-latest:moby/moby defines the line; source commit from docker/cli tag",
   "rationale":"Docker CLI tracks the latest stable moby/moby release; upstream publishes no GitHub release asset, so identity is the exact source tag/commit."},
 "docker_compose":{"channel":"latest-stable","source":"github-releases-latest:docker/compose + release asset digest",
   "rationale":"Accepted line is the latest non-prerelease GitHub release with its pinned release-asset digest."},
}

class ResolutionError(RuntimeError): pass

def http(url, headers=None, allow_401=False):
    h={"User-Agent":UA,"Accept":"application/json"}
    if headers: h.update(headers)
    if url.startswith("https://api.github.com/") and os.getenv("GITHUB_TOKEN"):
        h.setdefault("Authorization","Bearer "+os.environ["GITHUB_TOKEN"])
        h.setdefault("X-GitHub-Api-Version","2022-11-28")
    req=urllib.request.Request(url,headers=h)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return r.status,r.read(),{k.lower():v for k,v in r.headers.items()}
    except urllib.error.HTTPError as e:
        if e.code==401 and allow_401:
            return e.code,e.read(),{k.lower():v for k,v in e.headers.items()}
        raise ResolutionError(f"HTTP {e.code} resolving {url}") from e
    except urllib.error.URLError as e:
        raise ResolutionError(f"network error resolving {url}: {e.reason}") from e

def jget(url, headers=None):
    status,body,h=http(url,headers)
    if status!=200: raise ResolutionError(f"unexpected HTTP {status} for {url}")
    try: return json.loads(body),h
    except json.JSONDecodeError as e: raise ResolutionError(f"non-JSON response for {url}") from e

def latest(repo):
    data,_=jget(f"https://api.github.com/repos/{repo}/releases/latest")
    if data.get("draft") or data.get("prerelease"): raise ResolutionError(f"{repo} latest is not stable")
    if not data.get("tag_name"): raise ResolutionError(f"{repo} latest has no tag")
    return data

def strip_tag(tag):
    for p in ("docker-v","v"):
        if tag.startswith(p): tag=tag[len(p):]; break
    if not SEMVER.fullmatch(tag): raise ResolutionError(f"non-stable tag {tag}")
    return tag

def peel(repo,tag):
    enc=urllib.parse.quote(tag,safe="")
    data,_=jget(f"https://api.github.com/repos/{repo}/git/ref/tags/{enc}")
    obj=data.get("object",{})
    for _ in range(4):
        typ,sha=obj.get("type"),obj.get("sha")
        if typ=="commit" and isinstance(sha,str) and SHA40.fullmatch(sha): return sha
        if typ!="tag" or not isinstance(sha,str): break
        data,_=jget(f"https://api.github.com/repos/{repo}/git/tags/{sha}")
        obj=data.get("object",{})
    raise ResolutionError(f"cannot peel {repo}:{tag}")

def npm(name):
    enc=urllib.parse.quote(name,safe="")
    data,_=jget(f"https://registry.npmjs.org/{enc}/latest")
    v=data.get("version",""); dist=data.get("dist",{})
    if not SEMVER.fullmatch(v): raise ResolutionError(f"{name} npm latest is not stable")
    if not str(dist.get("integrity","")).startswith("sha512-"): raise ResolutionError(f"{name} lacks npm integrity")
    if not re.fullmatch(r"[0-9a-f]{40}",str(dist.get("shasum",""))): raise ResolutionError(f"{name} lacks npm shasum")
    return data

def npm_component(name,repo):
    n=npm(name); rel=latest(repo); rv=strip_tag(rel["tag_name"])
    if n["version"]!=rv: raise ResolutionError(f"{name} npm/GitHub stable mismatch: {n['version']} != {rv}")
    return {"version":n["version"],"npm":{"package":name,"integrity":n["dist"]["integrity"],"shasum":n["dist"]["shasum"]},
            "source":{"repository":repo,"tag":rel["tag_name"],"commit":peel(repo,rel["tag_name"])}},n

def ghcr_auth(challenge):
    m=re.match(r'Bearer\s+realm="([^"]+)"(?:,service="([^"]+)")?(?:,scope="([^"]+)")?',challenge)
    if not m: raise ResolutionError("unsupported GHCR auth challenge")
    realm,service,scope=m.groups(); q={k:v for k,v in (("service",service),("scope",scope)) if v}
    data,_=jget(realm+("?" + urllib.parse.urlencode(q) if q else ""))
    token=data.get("token") or data.get("access_token")
    if not token: raise ResolutionError("GHCR token missing")
    return token

def ghcr(path,token=None,accept=None):
    url="https://ghcr.io"+path; h={}
    if accept: h["Accept"]=accept
    if token: h["Authorization"]=f"Bearer {token}"
    status,body,rh=http(url,h,allow_401=token is None)
    if status==401 and token is None:
        token=ghcr_auth(rh.get("www-authenticate","")); h["Authorization"]=f"Bearer {token}"
        status,body,rh=http(url,h)
    if status!=200: raise ResolutionError(f"GHCR HTTP {status} for {path}")
    return json.loads(body),rh,token

def paseo_image(version):
    accept="application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
    top,h,token=ghcr(f"/v2/getpaseo/paseo/manifests/{version}",accept=accept)
    digest=h.get("docker-content-digest","")
    if not SHA256.fullmatch(digest): raise ResolutionError("Paseo GHCR tag has no immutable digest")
    manifest=top; amd=digest
    if isinstance(top.get("manifests"),list):
        matches=[x for x in top["manifests"] if x.get("platform",{}).get("os")=="linux" and x.get("platform",{}).get("architecture")=="amd64"]
        if len(matches)!=1 or not SHA256.fullmatch(str(matches[0].get("digest",""))): raise ResolutionError("Paseo GHCR lacks unique linux/amd64 manifest")
        amd=matches[0]["digest"]; manifest,_,token=ghcr(f"/v2/getpaseo/paseo/manifests/{amd}",token,accept)
    cfg=manifest.get("config",{}).get("digest","")
    if not SHA256.fullmatch(str(cfg)): raise ResolutionError("Paseo image config digest missing")
    config,_,_=ghcr(f"/v2/getpaseo/paseo/blobs/{cfg}",token)
    node=None
    for e in config.get("config",{}).get("Env",[]):
        if isinstance(e,str) and e.startswith("NODE_VERSION="): node=e.split("=",1)[1]
    if not node or not SEMVER.fullmatch(node): raise ResolutionError("Paseo image NODE_VERSION missing")
    return {"image":f"ghcr.io/getpaseo/paseo:{version}","digest":digest,"reference":f"ghcr.io/getpaseo/paseo@{digest}",
            "linux_amd64_manifest":amd,"config_digest":cfg,"node_version":node}

def asset(rel,pattern):
    found=[a for a in rel.get("assets",[]) if re.fullmatch(pattern,str(a.get("name","")))]
    if len(found)!=1: raise ResolutionError(f"expected one asset matching {pattern}")
    a=found[0]
    if not SHA256.fullmatch(str(a.get("digest",""))): raise ResolutionError(f"{a.get('name')} lacks sha256 digest")
    return {"name":a["name"],"digest":a["digest"],"size":a.get("size")}

def binary(repo,pattern):
    rel=latest(repo); v=strip_tag(rel["tag_name"])
    return {"version":v,"source":{"repository":repo,"tag":rel["tag_name"],"commit":peel(repo,rel["tag_name"])},
            "artifact":asset(rel,pattern.format(version=re.escape(v)))}

def release_by_tag(repo,tag):
    enc=urllib.parse.quote(tag,safe="")
    data,_=jget(f"https://api.github.com/repos/{repo}/releases/tags/{enc}")
    if data.get("draft") or data.get("prerelease"): raise ResolutionError(f"{repo} release {tag} is not stable")
    if data.get("tag_name")!=tag: raise ResolutionError(f"{repo} release tag mismatch for {tag}")
    return data

def npm_version(name,version):
    check_channel_substitution(version,f"{name} pinned version")
    enc=urllib.parse.quote(name,safe=""); ver=urllib.parse.quote(version,safe="")
    data,_=jget(f"https://registry.npmjs.org/{enc}/{ver}")
    dist=data.get("dist",{})
    if data.get("version")!=version: raise ResolutionError(f"{name} pinned {version} registry mismatch")
    if not str(dist.get("integrity","")).startswith("sha512-"): raise ResolutionError(f"{name} pinned {version} lacks npm integrity")
    if not re.fullmatch(r"[0-9a-f]{40}",str(dist.get("shasum",""))): raise ResolutionError(f"{name} pinned {version} lacks npm shasum")
    return data

def pinned_npm_component(name,repo,version):
    tag=f"v{version}"
    try: n=npm_version(name,version)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned {name} {version}: {e}") from e
    try:
        rel=release_by_tag(repo,tag); commit=peel(repo,tag)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned {name} {version}: {e}") from e
    if strip_tag(rel["tag_name"])!=version: raise ResolutionError(f"pinned {name} {version} GitHub tag mismatch")
    return {"version":version,"npm":{"package":name,"integrity":n["dist"]["integrity"],"shasum":n["dist"]["shasum"]},
            "source":{"repository":repo,"tag":rel["tag_name"],"commit":commit}},n

def pinned_binary(repo,pattern,version):
    tag=f"v{version}"
    try:
        rel=release_by_tag(repo,tag); commit=peel(repo,tag)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned {repo} {version}: {e}") from e
    if strip_tag(rel["tag_name"])!=version: raise ResolutionError(f"pinned {repo} {version} tag mismatch")
    try: art=asset(rel,pattern.format(version=re.escape(version)))
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned {repo} {version} artifact: {e}") from e
    return {"version":version,"source":{"repository":repo,"tag":rel["tag_name"],"commit":commit},"artifact":art}

def pinned_paseo_full(version):
    tag=f"v{version}"
    try:
        rel=release_by_tag("getpaseo/paseo",tag); commit=peel("getpaseo/paseo",tag)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned paseo {version}: {e}") from e
    if strip_tag(rel["tag_name"])!=version: raise ResolutionError(f"pinned paseo {version} tag mismatch")
    try: img=paseo_image(version)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned paseo {version} image: {e}") from e
    paseo={"version":version,"source":{"repository":"getpaseo/paseo","tag":rel["tag_name"],"commit":commit},"artifact":img}
    node={"version":img["node_version"],"minimum_for_pi":">=22.19.0","delivery":"provided-by-exact-paseo-image","immutable_parent":img["reference"]}
    return paseo,node

def pinned_docker(version):
    tag=f"v{version}"
    try: commit=peel("docker/cli",tag)
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned docker_cli {version}: {e}") from e
    try: peel("moby/moby",f"docker-v{version}")
    except ResolutionError as e: raise ResolutionError(f"cannot verify pinned docker_cli {version} stable line: {e}") from e
    return {"version":version,"source":{"repository":"docker/cli","tag":tag,"commit":commit},
            "stable_line_source":{"repository":"moby/moby","tag":f"docker-v{version}"},
            "artifact_identity":{"status":"source-commit-exact","digest":None,"reason":"docker/cli publishes release tags without GitHub release assets"}}

def playwright_chromium(version):
    _,body,_=http(f"https://raw.githubusercontent.com/microsoft/playwright/v{version}/packages/playwright-core/browsers.json")
    try: browsers=json.loads(body)
    except json.JSONDecodeError as e: raise ResolutionError(f"Playwright {version} browsers.json is not valid") from e
    chrom=[b for b in browsers.get("browsers",[]) if b.get("name")=="chromium"]
    if len(chrom)!=1: raise ResolutionError(f"Playwright {version} chromium identity missing")
    return {"revision":str(chrom[0].get("revision","")),"browser_version":str(chrom[0].get("browserVersion",""))}

def load_json_file(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError as e:
        raise ResolutionError(f"input file is missing: {path}") from e
    except OSError as e:
        raise ResolutionError(f"input file is unreadable: {path}") from e
    except json.JSONDecodeError as e:
        raise ResolutionError(f"input file is not valid JSON: {path}") from e

def inventory_component_set(definition):
    if not isinstance(definition,dict): raise ResolutionError("inventory definition must be an object")
    if definition.get("schema_version")!=1: raise ResolutionError("unsupported inventory schema")
    if definition.get("authority")!="environment_availability_only": raise ResolutionError("inventory authority must remain environment availability only")
    capabilities=definition.get("capabilities")
    if not isinstance(capabilities,list) or not capabilities: raise ResolutionError("inventory capabilities are missing")
    selected=set()
    for capability in capabilities:
        if not isinstance(capability,dict): raise ResolutionError("inventory capability entries must be objects")
        cid=capability.get("id")
        if not isinstance(cid,str) or not cid: raise ResolutionError("inventory capability id is invalid")
        if capability.get("approval")!="accepted": raise ResolutionError(f"capability is not accepted: {cid}")
        desired=capability.get("desired")
        if not isinstance(desired,dict) or not isinstance(desired.get("kind"),str):
            raise ResolutionError(f"unsupported desired-state selector: {cid}")
        if desired["kind"]=="candidate_component":
            component=desired.get("component")
            if not isinstance(component,str) or not component: raise ResolutionError(f"candidate component selector is invalid: {cid}")
            selected.add(component)
        elif desired["kind"] not in ("candidate_field","repo_tree"):
            raise ResolutionError(f"unsupported desired-state selector: {cid}")
    return selected

def check_capability_set(components, definition):
    selected=inventory_component_set(definition)
    if selected!=REQUIRED_COMPONENTS:
        raise ResolutionError("approved capability set changed: inventory candidate components differ from the resolver contract; new or removed global capabilities require explicit user approval")
    names=set(components)
    unknown=sorted(names-REQUIRED_COMPONENTS)
    if unknown: raise ResolutionError(f"changed capability set: unknown component(s) {','.join(unknown)} require explicit user approval")
    missing=sorted(REQUIRED_COMPONENTS-names)
    if missing: raise ResolutionError(f"mandatory component(s) missing: {','.join(missing)}")

def check_channel_substitution(value, where):
    if not isinstance(value,str) or not value:
        raise ResolutionError(f"{where} is not an accepted latest-stable version")
    if SEMVER.fullmatch(value): return
    low=value.lower()
    if "-" in value or "+" in value or any(m in low for m in CHANNEL_MARKERS):
        raise ResolutionError(f"prerelease/channel substitution rejected for {where}: only the accepted latest-stable line is allowed")
    raise ResolutionError(f"{where} is not an accepted latest-stable version")

def check_compatibility(comps):
    node_v=comps["node"].get("version","")
    try: tup=tuple(map(int,str(node_v).split(".")))
    except ValueError: raise ResolutionError("Node prerequisite is not a stable version")
    if tup < NODE_FLOOR: raise ResolutionError(f"incompatible coordinated set: Paseo Node {node_v} is below the Pi floor")
    if comps["node"].get("version")!=comps["paseo"].get("artifact",{}).get("node_version"):
        raise ResolutionError("incompatible coordinated set: Node version is not derived from the exact Paseo image")
    if comps["node"].get("immutable_parent")!=comps["paseo"].get("artifact",{}).get("reference"):
        raise ResolutionError("incompatible coordinated set: Node parent is not the exact Paseo image")
    for n in ("specpi","pi_mcp_adapter"):
        if comps[n].get("live_compatibility_smoke_required") is not True:
            raise ResolutionError(f"incompatible coordinated set: {n} lacks the required compatibility-smoke gate")
    peer=str(comps["pi_mcp_adapter"].get("declared_pi_ai_peer",""))
    marker=f"^0.{comps['pi']['version'].split('.')[1]}.0"
    if marker not in peer:
        raise ResolutionError(f"incompatible coordinated set: pi-mcp-adapter does not declare Pi {comps['pi']['version']} compatibility")

def authority_record_path(record):
    if not isinstance(record,str) or not record:
        raise ResolutionError("compatibility exception authority record must be a non-empty path")
    p=Path(record)
    if p.is_absolute(): return p
    base=ROOT.resolve(); target=(base/p).resolve()
    if target!=base and base not in target.parents:
        raise ResolutionError("compatibility exception authority record escapes the repository root")
    return target

def check_authority_binding(component,pinned_version,scope,rationale,authority):
    where=f"{component} {pinned_version}"
    if not isinstance(authority,dict):
        raise ResolutionError(f"compatibility exception for {where} lacks a bound authority record")
    digest=authority.get("digest")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}",str(digest or "")):
        raise ResolutionError(f"compatibility exception for {where} lacks a verifiable authority identity")
    try: raw=authority_record_path(authority.get("record")).read_bytes()
    except OSError as e:
        raise ResolutionError(f"compatibility exception authority record is unavailable for {where}") from e
    if "sha256:"+hashlib.sha256(raw).hexdigest()!=digest:
        raise ResolutionError(f"compatibility exception authority mismatch for {where}")
    try: data=json.loads(raw)
    except ValueError as e:
        raise ResolutionError(f"compatibility exception authority record is invalid for {where}") from e
    approvals=data.get("approvals") if isinstance(data,dict) else None
    if not isinstance(approvals,list):
        raise ResolutionError(f"compatibility exception authority record is invalid for {where}")
    for a in approvals:
        if not isinstance(a,dict): continue
        if (a.get("component")==component and a.get("pinned_version")==pinned_version
                and a.get("scope")==scope and a.get("rationale")==rationale):
            return {"record":authority.get("record"),"digest":digest}
    raise ResolutionError(f"compatibility exception for {where} has no matching authority approval")

def load_approved_exceptions(path):
    if path is None: return []
    data=load_json_file(path)
    if not isinstance(data,dict) or data.get("schema_version")!=1:
        raise ResolutionError("approved compatibility exceptions use an unsupported schema")
    entries=data.get("exceptions")
    if not isinstance(entries,list): raise ResolutionError("approved compatibility exceptions must list exception records")
    seen=set(); verified=[]
    for e in entries:
        if not isinstance(e,dict): raise ResolutionError("approved compatibility exception records must be objects")
        comp=e.get("component")
        if comp not in REQUIRED_COMPONENTS:
            raise ResolutionError("approved compatibility exception names an unknown component")
        if comp=="node":
            raise ResolutionError("derived component node cannot carry a compatibility exception; pin paseo")
        if comp in seen:
            raise ResolutionError(f"multiple approved compatibility exceptions for {comp}")
        seen.add(comp)
        pin=e.get("pinned_version","")
        check_channel_substitution(pin,"approved compatibility exception pinned version")
        for key in ("scope","rationale"):
            if not isinstance(e.get(key),str) or not e.get(key):
                raise ResolutionError(f"approved compatibility exception lacks durable field: {key}")
        authority=check_authority_binding(comp,pin,e["scope"],e["rationale"],e.get("authority"))
        verified.append({"component":comp,"pinned_version":pin,"scope":e["scope"],"rationale":e["rationale"],"authority":authority})
    return verified

def facts_digest(components, proposals, observed_latest):
    raw=json.dumps({"components":components,"compatibility_proposals":proposals,"observed_latest":observed_latest},
                   sort_keys=True,separators=(",",":")).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def evaluate_exceptions(components, proposals, observed_latest, approved):
    if not isinstance(proposals,list): raise ResolutionError("compatibility proposals must be a list")
    if not isinstance(observed_latest,dict): raise ResolutionError("observed latest facts must be an object")
    for comp, ver in observed_latest.items():
        if comp not in REQUIRED_COMPONENTS: raise ResolutionError("observed latest facts name an unknown component")
        check_channel_substitution(ver,f"observed latest {comp}")
    for p in proposals:
        if not isinstance(p,dict): raise ResolutionError("compatibility proposal records must be objects")
        if p.get("component") not in REQUIRED_COMPONENTS:
            raise ResolutionError("compatibility proposal names an unknown component")
        if p.get("component")=="node":
            raise ResolutionError("derived component node cannot carry a compatibility exception; pin paseo")
        check_channel_substitution(p.get("pinned_version",""),"compatibility proposal pinned version")
    by_pin={(e["component"],e["pinned_version"]): e for e in approved}
    embedded=[]
    covered=set()
    for p in proposals:
        key=(p["component"],p["pinned_version"])
        entry=by_pin.get(key)
        if entry is None:
            raise ResolutionError(f"compatibility exception for {p['component']} {p['pinned_version']} requires explicit user approval")
        covered.add(key)
        embedded.append((p["component"],entry))
    for comp in sorted(REQUIRED_COMPONENTS):
        if comp=="node": continue
        current=components[comp].get("version")
        latest_seen=observed_latest.get(comp)
        if latest_seen is not None and latest_seen!=current:
            key=(comp,current)
            entry=by_pin.get(key)
            if entry is None:
                raise ResolutionError(f"unapproved compatibility lag for {comp}: resolved {current} lags observed latest {latest_seen}; deliberate lag requires explicit user approval")
            if key not in covered:
                covered.add(key); embedded.append((comp,entry))
    for entry in approved:
        key=(entry["component"],entry["pinned_version"])
        if key in covered: continue
        current=components[entry["component"]].get("version")
        latest_seen=observed_latest.get(entry["component"])
        if current==entry["pinned_version"]:
            covered.add(key); embedded.append((entry["component"],entry))
        elif latest_seen is not None and latest_seen==current:
            covered.add(key); embedded.append((entry["component"],entry))
        else:
            raise ResolutionError(f"approved compatibility exception for {entry['component']} cannot be re-evaluated against the resolved facts without observed latest evidence")
    digest=facts_digest(components, proposals, observed_latest)
    records=[]
    for comp, entry in sorted(embedded):
        current=components[comp].get("version")
        latest_seen=observed_latest.get(comp)
        if latest_seen is None:
            if entry["pinned_version"]!=current:
                raise ResolutionError(f"approved compatibility exception for {comp} does not match the resolved facts")
            status="not_observed"
        elif latest_seen==current:
            status="no_longer_lagging"
        elif entry["pinned_version"]==current:
            status="still_required"
        else:
            raise ResolutionError(f"approved compatibility exception for {comp} does not match the resolved facts")
        records.append({"component":comp,"pinned_version":entry["pinned_version"],"scope":entry["scope"],
                        "rationale":entry["rationale"],"authority":entry["authority"],
                        "recheck":{"status":status,"observed_latest":latest_seen,"facts_digest":digest}})
    return records

def assemble_candidate(components, proposals, observed_latest, approved, definition):
    check_capability_set(components, definition)
    records=evaluate_exceptions(components, proposals, observed_latest, approved)
    comps=copy.deepcopy(components)
    for name in sorted(comps):
        comps[name]["stable_line"]=copy.deepcopy(STABLE_LINES[name])
    c={"schema_version":1,"policy":{"channel":"latest-stable","build_must_not_reresolve":True,
       "compatibility_exceptions":records,"generic_base_tooling":list(GENERIC_BASE_TOOLING),
       "generic_base_tooling_identity":GENERIC_BASE_TOOLING_IDENTITY},"components":comps}
    raw=json.dumps(c,sort_keys=True,separators=(",",":")).encode()
    c["candidate_id"]="sha256:"+hashlib.sha256(raw).hexdigest()
    validate(c, definition); return c

def facts_to_candidate(f, definition=None, approved=None):
    if not isinstance(f,dict) or not isinstance(f.get("components"),dict):
        raise ResolutionError("fixture facts must provide a components object")
    channel=f.get("channel")
    if channel is not None and channel!="latest-stable":
        raise ResolutionError("channel substitution rejected: only the accepted latest-stable channel is allowed")
    return assemble_candidate(f["components"], f.get("compatibility_proposals",[]),
                              f.get("observed_latest",{}), approved or [], definition)

def resolve_live(definition=None, approved=None):
    approved=approved or []
    pr=latest("getpaseo/paseo"); pv=strip_tag(pr["tag_name"]); img=paseo_image(pv)
    pi,_=npm_component("@earendil-works/pi-coding-agent","earendil-works/pi")
    pw,_=npm_component("playwright","microsoft/playwright")
    sp,_=npm_component("specpi","tannermidd/SpecPi")
    ad,adn=npm_component("pi-mcp-adapter","nicobailon/pi-mcp-adapter")
    pw["chromium"]=playwright_chromium(pw["version"])
    node=img["node_version"]
    peer=adn.get("peerDependencies",{}).get("@earendil-works/pi-ai","")
    ad["declared_pi_ai_peer"]=peer; ad["live_compatibility_smoke_required"]=True; sp["live_compatibility_smoke_required"]=True
    gh=binary("cli/cli",BINARY_PATTERNS["github_cli"])
    dc=binary("docker/compose",BINARY_PATTERNS["docker_compose"])
    er=latest("moby/moby"); dv=strip_tag(er["tag_name"])
    docker={"version":dv,"source":{"repository":"docker/cli","tag":f"v{dv}","commit":peel("docker/cli",f"v{dv}")},
            "stable_line_source":{"repository":"moby/moby","tag":er["tag_name"]},
            "artifact_identity":{"status":"source-commit-exact","digest":None,"reason":"docker/cli publishes release tags without GitHub release assets"}}
    components={
      "paseo":{"version":pv,"source":{"repository":"getpaseo/paseo","tag":pr["tag_name"],"commit":peel("getpaseo/paseo",pr["tag_name"])},"artifact":img},
      "node":{"version":node,"minimum_for_pi":">=22.19.0","delivery":"provided-by-exact-paseo-image","immutable_parent":img["reference"]},
      "pi":pi,"playwright":pw,"specpi":sp,"pi_mcp_adapter":ad,"github_cli":gh,"docker_cli":docker,"docker_compose":dc}
    observed={name: comp["version"] for name, comp in components.items()}
    for entry in approved:
        comp,pin=entry["component"],entry["pinned_version"]
        if pin==observed[comp]: continue
        if comp=="paseo":
            components["paseo"],components["node"]=pinned_paseo_full(pin)
        elif comp in EXPECTED_NPM_PACKAGE:
            c,ndata=pinned_npm_component(EXPECTED_NPM_PACKAGE[comp],EXPECTED_SOURCE_REPO[comp],pin)
            if comp=="playwright":
                try: c["chromium"]=playwright_chromium(pin)
                except ResolutionError as e: raise ResolutionError(f"cannot verify pinned playwright {pin} chromium: {e}") from e
            if comp in ("specpi","pi_mcp_adapter"): c["live_compatibility_smoke_required"]=True
            if comp=="pi_mcp_adapter": c["declared_pi_ai_peer"]=ndata.get("peerDependencies",{}).get("@earendil-works/pi-ai","")
            components[comp]=c
        elif comp in BINARY_PATTERNS:
            components[comp]=pinned_binary(EXPECTED_SOURCE_REPO[comp],BINARY_PATTERNS[comp],pin)
        elif comp=="docker_cli":
            components[comp]=pinned_docker(pin)
        else:
            raise ResolutionError(f"approved compatibility exception for {comp} cannot be resolved live")
    return assemble_candidate(components, [], observed, approved, definition)

def validate(c, definition=None):
    if definition is None:
        try: definition=load_json_file(DEFAULT_INVENTORY)
        except ResolutionError as e: raise ResolutionError(f"current approved inventory is unavailable: {e}") from e
    comps=c.get("components",{})
    if c.get("schema_version")!=1: raise ResolutionError("unsupported candidate schema")
    check_capability_set(comps, definition)
    policy=c.get("policy",{})
    if policy.get("channel")!="latest-stable": raise ResolutionError("candidate channel must remain latest-stable")
    if policy.get("build_must_not_reresolve") is not True: raise ResolutionError("candidate must forbid build-time latest re-resolution")
    if policy.get("generic_base_tooling")!=GENERIC_BASE_TOOLING: raise ResolutionError("generic base tooling set changed")
    if policy.get("generic_base_tooling_identity")!=GENERIC_BASE_TOOLING_IDENTITY: raise ResolutionError("generic base tooling identity changed")
    for n in sorted(comps):
        check_channel_substitution(comps[n].get("version",""),f"{n} version")
    for n in ("pi","playwright","specpi","pi_mcp_adapter"):
        npmdata=comps[n].get("npm",{})
        if npmdata.get("package")!=EXPECTED_NPM_PACKAGE[n]: raise ResolutionError(f"{n} npm package substitution rejected")
        if not str(npmdata.get("integrity","")).startswith("sha512-") or not re.fullmatch(r"[0-9a-f]{40}",str(npmdata.get("shasum",""))):
            raise ResolutionError(f"{n} npm integrity missing")
    for n in sorted(EXPECTED_SOURCE_REPO):
        src=comps[n].get("source",{})
        if src.get("repository")!=EXPECTED_SOURCE_REPO[n]: raise ResolutionError(f"{n} source substitution rejected")
        try: tag_version=strip_tag(str(src.get("tag","")))
        except ResolutionError: raise ResolutionError(f"{n} source tag is not an accepted stable tag")
        if tag_version!=comps[n]["version"]: raise ResolutionError(f"{n} source tag does not match the frozen version")
        if not SHA40.fullmatch(str(src.get("commit",""))): raise ResolutionError(f"{n} source commit missing")
    sls=comps["docker_cli"].get("stable_line_source",{})
    if sls.get("repository")!="moby/moby": raise ResolutionError("docker stable-line source substitution rejected")
    try: docker_line=strip_tag(str(sls.get("tag","")))
    except ResolutionError: raise ResolutionError("docker stable-line tag is not an accepted stable tag")
    if docker_line!=comps["docker_cli"]["version"]: raise ResolutionError("docker stable-line tag does not match the frozen version")
    pa=comps["paseo"].get("artifact",{})
    if not SHA256.fullmatch(str(pa.get("digest",""))): raise ResolutionError("Paseo official immutable GHCR identity missing")
    if str(pa.get("reference",""))!=f"ghcr.io/getpaseo/paseo@{pa.get('digest','')}": raise ResolutionError("Paseo GHCR reference must pin the immutable digest")
    if str(pa.get("image",""))!=f"ghcr.io/getpaseo/paseo:{comps['paseo']['version']}": raise ResolutionError("Paseo image tag does not match the frozen version")
    if not SHA256.fullmatch(str(pa.get("linux_amd64_manifest",""))): raise ResolutionError("Paseo linux/amd64 manifest identity missing")
    if not SHA256.fullmatch(str(pa.get("config_digest",""))): raise ResolutionError("Paseo image config digest missing")
    check_channel_substitution(str(pa.get("node_version","")),"Paseo image Node version")
    node=comps["node"]
    if node.get("delivery")!="provided-by-exact-paseo-image": raise ResolutionError("Node delivery substitution rejected")
    if node.get("minimum_for_pi")!=">=22.19.0": raise ResolutionError("Node prerequisite floor changed")
    for n in ("github_cli","docker_compose"):
        if not SHA256.fullmatch(str(comps[n].get("artifact",{}).get("digest",""))): raise ResolutionError(f"{n} artifact digest missing")
    gh_name=str(comps["github_cli"].get("artifact",{}).get("name",""))
    if gh_name!=f"gh_{comps['github_cli']['version']}_linux_amd64.tar.gz": raise ResolutionError("github_cli artifact substitution rejected")
    if str(comps["docker_compose"].get("artifact",{}).get("name",""))!="docker-compose-linux-x86_64":
        raise ResolutionError("docker_compose artifact substitution rejected")
    if not comps["playwright"].get("chromium",{}).get("revision") or not comps["playwright"].get("chromium",{}).get("browser_version"):
        raise ResolutionError("Playwright/Chromium identity missing")
    check_compatibility(comps)
    for n in sorted(comps):
        if "stable_line" in comps[n] and comps[n]["stable_line"]!=STABLE_LINES[n]:
            raise ResolutionError(f"{n} stable-line rationale substitution rejected")
    exceptions=policy.get("compatibility_exceptions",[])
    if not isinstance(exceptions,list): raise ResolutionError("compatibility exceptions must be a list")
    for e in exceptions:
        if not isinstance(e,dict): raise ResolutionError("compatibility exception records must be objects")
        if e.get("component") not in REQUIRED_COMPONENTS: raise ResolutionError("compatibility exception names an unknown component")
        check_channel_substitution(e.get("pinned_version",""),"compatibility exception pinned version")
        for key in ("scope","rationale"):
            if not isinstance(e.get(key),str) or not e.get(key):
                raise ResolutionError(f"compatibility exception lacks durable field: {key}")
        check_authority_binding(e["component"],e["pinned_version"],e["scope"],e["rationale"],e.get("authority"))
        recheck=e.get("recheck",{})
        if recheck.get("status") not in ("still_required","no_longer_lagging","not_observed"):
            raise ResolutionError("compatibility exception lacks re-evaluation status")
        observed=recheck.get("observed_latest")
        if observed is not None: check_channel_substitution(observed,"compatibility exception observed latest")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}",str(recheck.get("facts_digest",""))):
            raise ResolutionError("compatibility exception lacks deterministic re-evaluation identity")
        current=comps[e["component"]]["version"]
        if recheck["status"] in ("still_required","not_observed") and e["pinned_version"]!=current:
            raise ResolutionError("compatibility exception does not match the frozen component version")
        if recheck["status"]=="no_longer_lagging" and observed!=current:
            raise ResolutionError("compatibility exception re-evaluation status is inconsistent")
    tmp=json.loads(json.dumps(c)); claimed=tmp.pop("candidate_id",None)
    expected="sha256:"+hashlib.sha256(json.dumps(tmp,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if claimed!=expected: raise ResolutionError("candidate_id mismatch")
    low=json.dumps(c,sort_keys=True).lower()
    for key in ('"password"','"authorization"','"access_token"','"private_key"','"secret"'):
        if key in low: raise ResolutionError(f"secret-bearing field forbidden: {key}")

def atomic_write(path,c):
    path.parent.mkdir(parents=True,exist_ok=True); rendered=json.dumps(c,sort_keys=True,indent=2)+"\n"
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w") as h: h.write(rendered); h.flush(); os.fsync(h.fileno())
        os.replace(tmp,path)
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

def accepted_candidate_path(definition):
    source=definition.get("candidate_source")
    if not isinstance(source,str) or not source or Path(source).is_absolute():
        raise ResolutionError("inventory candidate_source is invalid")
    base=ROOT.resolve(); target=(base/Path(source)).resolve()
    if target!=base and base not in target.parents:
        raise ResolutionError("inventory candidate_source escapes the repository root")
    return target

def guard_output_path(output, definition, inputs):
    resolved=Path(output).resolve()
    if resolved==accepted_candidate_path(definition):
        raise ResolutionError("refuses to overwrite the accepted candidate; staged output must use a separate path and promotion is owned by the staged update path")
    for role, other in inputs:
        if other is not None and Path(other).resolve()==resolved:
            raise ResolutionError(f"refuses to overwrite resolver input {role}")
    return Path(output)

def main():
    ap=argparse.ArgumentParser(description="Resolve the coordinated latest-stable maintenance candidate and freeze one exact immutable record.",
        epilog="Default output is read-only stdout. --output stages to a separate path and can never overwrite the accepted candidate; promotion is owned by the staged update path. Resolution does not reconcile current state, run doctor checks, build images, or promote production.")
    ap.add_argument("--output",default=None,help="staging path for the frozen candidate; never the accepted candidate (default: read-only stdout)")
    ap.add_argument("--check",action="store_true",help="read-only: print the resolved candidate without writing")
    ap.add_argument("--fixture",type=Path); ap.add_argument("--validate",type=Path); ap.add_argument("--readback",type=Path)
    ap.add_argument("--inventory",type=Path,default=DEFAULT_INVENTORY)
    ap.add_argument("--approved-exceptions",type=Path)
    a=ap.parse_args()
    try:
        definition=load_json_file(a.inventory)
        approved=load_approved_exceptions(a.approved_exceptions)
        target=a.validate or a.readback
        if target:
            c=load_json_file(target); validate(c, definition); print(c["candidate_id"]); return 0
        c=facts_to_candidate(load_json_file(a.fixture), definition, approved) if a.fixture else resolve_live(definition, approved)
        if a.check or a.output is None: print(json.dumps(c,sort_keys=True,indent=2))
        else:
            out=guard_output_path(a.output, definition, [("fixture",a.fixture),("inventory",a.inventory),("approved-exceptions",a.approved_exceptions)])
            atomic_write(out,c); print(c["candidate_id"])
        return 0
    except (ResolutionError,KeyError,TypeError,ValueError,OSError) as e:
        print(f"candidate resolution failed: {e}",file=os.sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
