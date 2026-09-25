#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, os, re, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path

SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA256=re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER=re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
UA="pi-unraid-paseo-candidate-resolver/1"

class ResolutionError(RuntimeError): pass

def http(url, headers=None, allow_401=False):
    h={"User-Agent":UA,"Accept":"application/json"}
    if headers: h.update(headers)
    if url.startswith("https://api.github.com/") and os.getenv("GITHUB_TOKEN"):
        h.setdefault("Authorization",f"Bearer {os.environ['GITHUB_TOKEN']}")
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

def facts_to_candidate(f):
    components=f["components"]
    c={"schema_version":1,"policy":{"channel":"latest-stable","build_must_not_reresolve":True,"compatibility_exceptions":[],
       "generic_base_tooling":["bash","git","network-tools","build-tools","python3"],
       "generic_base_tooling_identity":"owned by the exact Paseo child-image package graph; not independent floating version lines"},
       "components":components}
    raw=json.dumps(c,sort_keys=True,separators=(",",":")).encode()
    c["candidate_id"]="sha256:"+hashlib.sha256(raw).hexdigest()
    validate(c); return c

def resolve_live():
    pr=latest("getpaseo/paseo"); pv=strip_tag(pr["tag_name"]); img=paseo_image(pv)
    pi,_=npm_component("@earendil-works/pi-coding-agent","earendil-works/pi")
    pw,_=npm_component("playwright","microsoft/playwright")
    sp,_=npm_component("specpi","tannermidd/SpecPi")
    ad,adn=npm_component("pi-mcp-adapter","nicobailon/pi-mcp-adapter")
    _,body,_=http(f"https://raw.githubusercontent.com/microsoft/playwright/v{pw['version']}/packages/playwright-core/browsers.json")
    browsers=json.loads(body); chrom=[b for b in browsers.get("browsers",[]) if b.get("name")=="chromium"]
    if len(chrom)!=1: raise ResolutionError("Playwright chromium identity missing")
    pw["chromium"]={"revision":str(chrom[0].get("revision","")),"browser_version":str(chrom[0].get("browserVersion",""))}
    node=img["node_version"]
    if tuple(map(int,node.split("."))) < (22,19,0): raise ResolutionError(f"Paseo Node {node} is too old for Pi")
    peer=adn.get("peerDependencies",{}).get("@earendil-works/pi-ai","")
    marker=f"^0.{pi['version'].split('.')[1]}.0"
    if marker not in peer: raise ResolutionError(f"pi-mcp-adapter does not declare Pi {pi['version']} compatibility")
    ad["declared_pi_ai_peer"]=peer; ad["live_compatibility_smoke_required"]=True; sp["live_compatibility_smoke_required"]=True
    gh=binary("cli/cli",r"gh_{version}_linux_amd64\.tar\.gz")
    dc=binary("docker/compose",r"docker-compose-linux-x86_64")
    er=latest("moby/moby"); dv=strip_tag(er["tag_name"])
    docker={"version":dv,"source":{"repository":"docker/cli","tag":f"v{dv}","commit":peel("docker/cli",f"v{dv}")},
            "stable_line_source":{"repository":"moby/moby","tag":er["tag_name"]},
            "artifact_identity":{"status":"source-commit-exact","digest":None,"reason":"docker/cli publishes release tags without GitHub release assets"}}
    facts={"components":{
      "paseo":{"version":pv,"source":{"repository":"getpaseo/paseo","tag":pr["tag_name"],"commit":peel("getpaseo/paseo",pr["tag_name"])},"artifact":img},
      "node":{"version":node,"minimum_for_pi":">=22.19.0","delivery":"provided-by-exact-paseo-image","immutable_parent":img["reference"]},
      "pi":pi,"playwright":pw,"specpi":sp,"pi_mcp_adapter":ad,"github_cli":gh,"docker_cli":docker,"docker_compose":dc}}
    return facts_to_candidate(facts)

def validate(c):
    req={"paseo","node","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"}
    comps=c.get("components",{})
    if c.get("schema_version")!=1 or set(comps)!=req: raise ResolutionError("candidate component coverage incomplete")
    for n,x in comps.items():
        if not isinstance(x.get("version"),str) or not x["version"]: raise ResolutionError(f"{n} exact version missing")
    for n in ("pi","playwright","specpi","pi_mcp_adapter"):
        npmdata=comps[n].get("npm",{})
        if not str(npmdata.get("integrity","")).startswith("sha512-") or not re.fullmatch(r"[0-9a-f]{40}",str(npmdata.get("shasum",""))):
            raise ResolutionError(f"{n} npm integrity missing")
    for n in ("paseo","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"):
        if not SHA40.fullmatch(str(comps[n].get("source",{}).get("commit",""))): raise ResolutionError(f"{n} source commit missing")
    pa=comps["paseo"].get("artifact",{})
    if not SHA256.fullmatch(str(pa.get("digest",""))) or not str(pa.get("reference","")).startswith("ghcr.io/getpaseo/paseo@sha256:"):
        raise ResolutionError("Paseo official immutable GHCR identity missing")
    for n in ("github_cli","docker_compose"):
        if not SHA256.fullmatch(str(comps[n].get("artifact",{}).get("digest",""))): raise ResolutionError(f"{n} artifact digest missing")
    if tuple(map(int,comps["node"]["version"].split("."))) < (22,19,0): raise ResolutionError("Node prerequisite too old")
    if not comps["playwright"].get("chromium",{}).get("revision") or not comps["playwright"].get("chromium",{}).get("browser_version"):
        raise ResolutionError("Playwright/Chromium identity missing")
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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="config/paseo-candidate.json")
    ap.add_argument("--check",action="store_true"); ap.add_argument("--fixture",type=Path); ap.add_argument("--validate",type=Path)
    a=ap.parse_args()
    try:
        if a.validate:
            c=json.loads(a.validate.read_text()); validate(c); print(c["candidate_id"]); return 0
        c=facts_to_candidate(json.loads(a.fixture.read_text())) if a.fixture else resolve_live()
        if a.check: print(json.dumps(c,sort_keys=True,indent=2))
        else: atomic_write(Path(a.output),c); print(c["candidate_id"])
        return 0
    except (ResolutionError,KeyError,TypeError,ValueError,json.JSONDecodeError) as e:
        print(f"candidate resolution failed: {e}",file=os.sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
