
login = {};
login.NAME = "login";    // The name of this namespace

// This function (c) 2002-2005 Chris Veness
//
login.sha1Hash = function(msg)
{
    // constants [§4.2.1]
    var K = [0x5a827999, 0x6ed9eba1, 0x8f1bbcdc, 0xca62c1d6];


    // PREPROCESSING 
 
    msg += String.fromCharCode(0x80); // add trailing '1' bit to string [§5.1.1]

    // convert string msg into 512-bit/16-integer blocks arrays of ints [§5.2.1]
    var l = Math.ceil(msg.length/4) + 2;  // long enough to contain msg plus 2-word length
    var N = Math.ceil(l/16);              // in N 16-int blocks
    var M = new Array(N);
    for (var i=0; i<N; i++) {
        M[i] = new Array(16);
        for (var j=0; j<16; j++) {  // encode 4 chars per integer, big-endian encoding
            M[i][j] = (msg.charCodeAt(i*64+j*4)<<24) | (msg.charCodeAt(i*64+j*4+1)<<16) | 
                      (msg.charCodeAt(i*64+j*4+2)<<8) | (msg.charCodeAt(i*64+j*4+3));
        }
    }
    // add length (in bits) into final pair of 32-bit integers (big-endian) [5.1.1]
    // note: most significant word would be ((len-1)*8 >>> 32, but since JS converts
    // bitwise-op args to 32 bits, we need to simulate this by arithmetic operators
    M[N-1][14] = ((msg.length-1)*8) / Math.pow(2, 32); M[N-1][14] = Math.floor(M[N-1][14])
    M[N-1][15] = ((msg.length-1)*8) & 0xffffffff;

    // set initial hash value [§5.3.1]
    var H0 = 0x67452301;
    var H1 = 0xefcdab89;
    var H2 = 0x98badcfe;
    var H3 = 0x10325476;
    var H4 = 0xc3d2e1f0;

    // HASH COMPUTATION [§6.1.2]

    var W = new Array(80); var a, b, c, d, e;
    for (var i=0; i<N; i++) {

        // 1 - prepare message schedule 'W'
        for (var t=0;  t<16; t++) W[t] = M[i][t];
        for (var t=16; t<80; t++) W[t] = login.ROTL(W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1);

        // 2 - initialise five working variables a, b, c, d, e with previous hash value
        a = H0; b = H1; c = H2; d = H3; e = H4;

        // 3 - main loop
        for (var t=0; t<80; t++) {
            var s = Math.floor(t/20); // seq for blocks of 'f' functions and 'K' constants
            var T = (login.ROTL(a,5) + login.f(s,b,c,d) + e + K[s] + W[t]) & 0xffffffff;
            e = d;
            d = c;
            c = login.ROTL(b, 30);
            b = a;
            a = T;
        }

        // 4 - compute the new intermediate hash value
        H0 = (H0+a) & 0xffffffff;  // note 'addition modulo 2^32'
        H1 = (H1+b) & 0xffffffff; 
        H2 = (H2+c) & 0xffffffff; 
        H3 = (H3+d) & 0xffffffff; 
        H4 = (H4+e) & 0xffffffff;
    }

    //return H0.toHexStr() + H1.toHexStr() + H2.toHexStr() + H3.toHexStr() + H4.toHexStr();
    return H0.toByteStr() + H1.toByteStr() + H2.toByteStr() + H3.toByteStr() + H4.toByteStr();
}

//
// function 'f' [§4.1.1]
//
login.f = function(s, x, y, z) 
{
    switch (s) {
    case 0: return (x & y) ^ (~x & z);           // Ch()
    case 1: return x ^ y ^ z;                    // Parity()
    case 2: return (x & y) ^ (x & z) ^ (y & z);  // Maj()
    case 3: return x ^ y ^ z;                    // Parity()
    }
}

//
// rotate left (circular left shift) value x by n positions [§3.2.5]
//
login.ROTL = function(x, n)
{
    return (x<<n) | (x>>>(32-n));
}

//
// extend Number class with a tailored hex-string method 
//   (note toString(16) is implementation-dependant, and 
//   in IE returns signed numbers when used on full words)
//
Number.prototype.toHexStr = function()
{
    var s="", v;
    for (var i=7; i>=0; i--) { v = (this>>>(i*4)) & 0xf; s += v.toString(16); }
    return s;
}

// End Chris Veness's code.

Number.prototype.toByteStr = function()
{
    var s="", v;
    for (var i=3; i>=0; i--) { v = (this>>>(i*8)) & 0xff; s += login.charCode(v); }
    return s;
}

login.charOrd = function(a) {return a.charCodeAt(0); };
login.charCode = function(x) {return String.fromCharCode(x); };

login.strXor = function(s1, s2) 
{
  var r = [];
  var a = Array.prototype.map.call(s1, login.charOrd);
  var b = Array.prototype.map.call(s2, login.charOrd);
  for (var i=0; i < a.length; i++) {
    r.push((a[i] ^ b[i]) & 0xff);
    }
  var c = Array.prototype.map.call(r, login.charCode);
  return c.join("");
}

login.HMAC_SHA1 = function(key, message) 
{
  var blocksize = 64;
  var ipad = "6666666666666666666666666666666666666666666666666666666666666666";
  var opad = "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\" + 
      "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\";
  if (key.length > blocksize) {
    key = login.sha1Hash(key);
  }
  var ka = Array.prototype.map.call(key, login.charOrd);
  for (var i=key.length; i < blocksize; i++) {
    ka.push(0);
  }
  key = ka.map(login.charCode).join("");
  return login.sha1Hash(login.strXor(key, opad) +  login.sha1Hash(login.strXor(key, ipad) + message));
}


login.encodeFormData = function(data) {
    var pairs = [];
    var regexp = /%20/g;
    for (var name in data) {
        var value = data[name].toString();
        var pair = escape(name).replace(regexp, "+") + "=" + 
                    escape(value).replace(regexp, "+");
        pairs.push(pair);
    };
    return pairs.join("&");
};

login.submitForm = function() {
  var data = {};
  var username_el = document.getElementById("id_username")
  if (username_el.value.length == 0) {
      return false};
  data.redir = document.getElementById("id_redir").value
  data.username = username_el.value
  var key = document.getElementById("id_key").value
  data.key = key // key is urlencoded, send it back that way.
  var password_el = document.getElementById("id_password");
  if (password_el.value.length == 0) {
      return false};
  data.password = login.HMAC_SHA1(unescape(key), password_el.value);
  password_el.value = "";
  // Now send the form using async request.
  var req = new XMLHttpRequest();
  req.onreadystatechange = function() {
          if (req.readyState == 4) {
              if (req.status == 200) {
                  // response is JSON 2-tuple of (code, path_or_error)
                  var arr = eval("(" + req.responseText + ")"); 
                  if (arr[0] == 401) {
                      alert(arr[1]);
                  };
                  if (arr[0] == 200) {
                      // equivalent of a redirect
                      window.location.pathname = arr[1];
                  };
              }
              else {
                  console.log("login failed:", req.status, req.statusText);
              };
          };
     };
  req.open("POST", "/auth/login");
  req.setRequestHeader("X-Requested-With", "XMLHttpRequest");
  req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  req.send(login.encodeFormData(data));
  return false;
}

