// One writer shared by the auth component and the ready/reload boundary.
// Commands are ordered so an older iframe cannot overwrite a rotated token.
function applyCosterlyAuthWrite(host, args) {
  const key = 'costerly.supabase.session.v1';
  const cookie = '__Host-costerly-resume-v1';
  try {
    const stamp = BigInt(args.issuedAt || '0');
    const last = host.__costerlyAuthWrite;
    if (last && (stamp < last.stamp ||
        (stamp === last.stamp && args.requestId === last.requestId))) return {ok:true};
    if (args.action === 'store' && args.session) {
      host.sessionStorage.setItem(key, JSON.stringify(args.session));
    } else if (args.action === 'clear') {
      host.sessionStorage.removeItem(key);
      host.sessionStorage.removeItem(key + ':recovery');
      host.sessionStorage.removeItem(key + ':confirmation');
    }
    if (args.action === 'clear') {
      host.document.cookie = `${cookie}=; Max-Age=0; Path=/; Secure; SameSite=None; Partitioned`;
    } else if (args.resumeBlob) {
      host.document.cookie = `${cookie}=${encodeURIComponent(args.resumeBlob)}; Max-Age=1800; Path=/; Secure; SameSite=None; Partitioned`;
    }
    host.__costerlyAuthWrite = {stamp, requestId:args.requestId};
    return {ok:true};
  } catch (_) {
    return {ok:false};
  }
}
