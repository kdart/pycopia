

// This function (c) 2002-2005 Chris Veness
//
function sha1Hash(msg)
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
        for (var t=16; t<80; t++) W[t] = ROTL(W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1);

        // 2 - initialise five working variables a, b, c, d, e with previous hash value
        a = H0; b = H1; c = H2; d = H3; e = H4;

        // 3 - main loop
        for (var t=0; t<80; t++) {
            var s = Math.floor(t/20); // seq for blocks of 'f' functions and 'K' constants
            var T = (ROTL(a,5) + f(s,b,c,d) + e + K[s] + W[t]) & 0xffffffff;
            e = d;
            d = c;
            c = ROTL(b, 30);
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
function f(s, x, y, z) 
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
function ROTL(x, n)
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
    for (var i=3; i>=0; i--) { v = (this>>>(i*8)) & 0xff; s += charCode(v); }
    return s;
}

function charOrd(a) {return a.charCodeAt(0); };
function charCode(x) {return String.fromCharCode(x); };

function strXor(s1, s2) {
  var r = [];
  var a = Array.prototype.map.call(s1, charOrd);
  var b = Array.prototype.map.call(s2, charOrd);
  for (var i=0; i < a.length; i++) {
    r.push((a[i] ^ b[i]) & 0xff);
    }
  var c = Array.prototype.map.call(r, charCode);
  return c.join("");
}

function str2hex(s) {
  var r = [];
  for (var i=0; i < s.length; i++) {
    r[i] = s.charCodeAt(i).toString(16);
  }
  return "\\x" + r.join("\\x")
}

function HMAC_SHA1(key, message) {
  var blocksize = 64;
  var ipad = "6666666666666666666666666666666666666666666666666666666666666666";
  var opad = "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\" + 
      "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\";
  if (key.length > blocksize) {
    key = sha1Hash(key);
  }
  var ka = Array.prototype.map.call(key, charOrd);
  for (var i=key.length; i < blocksize; i++) {
    ka.push(0);
  }
  key = ka.map(charCode).join("");
  return sha1Hash(strXor(key, opad) +  sha1Hash(strXor(key, ipad) + message));
}


function validateForm() {
  if (document.getElementById("id_username").value.length == 0) {return false};
  var pwe = document.getElementById("id_password");
  if (pwe.value.length == 0) {return false};
  pwe.value = escape(HMAC_SHA1(unescape(document.getElementById("id_key").value), pwe.value));
  return true;
}


