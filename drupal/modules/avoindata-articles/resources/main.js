!function(t){var n={};function r(e){if(n[e])return n[e].exports;var o=n[e]={i:e,l:!1,exports:{}};return t[e].call(o.exports,o,o.exports,r),o.l=!0,o.exports}r.m=t,r.c=n,r.d=function(t,n,e){r.o(t,n)||Object.defineProperty(t,n,{enumerable:!0,get:e})},r.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},r.t=function(t,n){if(1&n&&(t=r(t)),8&n)return t;if(4&n&&"object"==typeof t&&t&&t.__esModule)return t;var e=Object.create(null);if(r.r(e),Object.defineProperty(e,"default",{enumerable:!0,value:t}),2&n&&"string"!=typeof t)for(var o in t)r.d(e,o,function(n){return t[n]}.bind(null,o));return e},r.n=function(t){var n=t&&t.__esModule?function(){return t.default}:function(){return t};return r.d(n,"a",n),n},r.o=function(t,n){return Object.prototype.hasOwnProperty.call(t,n)},r.p="",r(r.s=32)}([function(t,n,r){var e=r(21)("wks"),o=r(14),i=r(2).Symbol,c="function"==typeof i;(t.exports=function(t){return e[t]||(e[t]=c&&i[t]||(c?i:o)("Symbol."+t))}).store=e},function(t,n,r){var e=r(4),o=r(13);t.exports=r(6)?function(t,n,r){return e.f(t,n,o(1,r))}:function(t,n,r){return t[n]=r,t}},function(t,n){var r=t.exports="undefined"!=typeof window&&window.Math==Math?window:"undefined"!=typeof self&&self.Math==Math?self:Function("return this")();"number"==typeof __g&&(__g=r)},function(t,n){t.exports={}},function(t,n,r){var e=r(5),o=r(34),i=r(35),c=Object.defineProperty;n.f=r(6)?Object.defineProperty:function(t,n,r){if(e(t),n=i(n,!0),e(r),o)try{return c(t,n,r)}catch(t){}if("get"in r||"set"in r)throw TypeError("Accessors not supported!");return"value"in r&&(t[n]=r.value),t}},function(t,n,r){var e=r(11);t.exports=function(t){if(!e(t))throw TypeError(t+" is not an object!");return t}},function(t,n,r){t.exports=!r(12)(function(){return 7!=Object.defineProperty({},"a",{get:function(){return 7}}).a})},function(t,n,r){var e=r(2),o=r(1),i=r(8),c=r(14)("src"),u=Function.toString,a=(""+u).split("toString");r(9).inspectSource=function(t){return u.call(t)},(t.exports=function(t,n,r,u){var f="function"==typeof r;f&&(i(r,"name")||o(r,"name",n)),t[n]!==r&&(f&&(i(r,c)||o(r,c,t[n]?""+t[n]:a.join(String(n)))),t===e?t[n]=r:u?t[n]?t[n]=r:o(t,n,r):(delete t[n],o(t,n,r)))})(Function.prototype,"toString",function(){return"function"==typeof this&&this[c]||u.call(this)})},function(t,n){var r={}.hasOwnProperty;t.exports=function(t,n){return r.call(t,n)}},function(t,n){var r=t.exports={version:"2.5.7"};"number"==typeof __e&&(__e=r)},function(t,n){t.exports=function(t){if(void 0==t)throw TypeError("Can't call method on  "+t);return t}},function(t,n){t.exports=function(t){return"object"==typeof t?null!==t:"function"==typeof t}},function(t,n){t.exports=function(t){try{return!!t()}catch(t){return!0}}},function(t,n){t.exports=function(t,n){return{enumerable:!(1&t),configurable:!(2&t),writable:!(4&t),value:n}}},function(t,n){var r=0,e=Math.random();t.exports=function(t){return"Symbol(".concat(void 0===t?"":t,")_",(++r+e).toString(36))}},function(t,n){var r=Math.ceil,e=Math.floor;t.exports=function(t){return isNaN(t=+t)?0:(t>0?e:r)(t)}},function(t,n,r){var e=r(43),o=r(10);t.exports=function(t){return e(o(t))}},function(t,n,r){var e=r(21)("keys"),o=r(14);t.exports=function(t){return e[t]||(e[t]=o(t))}},function(t,n,r){"use strict";var e=r(60),o=r(61),i=r(62);function c(t,n){return n.encode?n.strict?e(t):encodeURIComponent(t):t}function u(t){var n=t.indexOf("?");return-1===n?"":t.slice(n+1)}function a(t,n){var r=function(t){var n;switch(t.arrayFormat){case"index":return function(t,r,e){n=/\[(\d*)\]$/.exec(t),t=t.replace(/\[\d*\]$/,""),n?(void 0===e[t]&&(e[t]={}),e[t][n[1]]=r):e[t]=r};case"bracket":return function(t,r,e){n=/(\[\])$/.exec(t),t=t.replace(/\[\]$/,""),n?void 0!==e[t]?e[t]=[].concat(e[t],r):e[t]=[r]:e[t]=r};default:return function(t,n,r){void 0!==r[t]?r[t]=[].concat(r[t],n):r[t]=n}}}(n=o({arrayFormat:"none"},n)),e=Object.create(null);return"string"!=typeof t?e:(t=t.trim().replace(/^[?#&]/,""))?(t.split("&").forEach(function(t){var n=t.replace(/\+/g," ").split("="),o=n.shift(),c=n.length>0?n.join("="):void 0;c=void 0===c?null:i(c),r(i(o),c,e)}),Object.keys(e).sort().reduce(function(t,n){var r=e[n];return Boolean(r)&&"object"==typeof r&&!Array.isArray(r)?t[n]=function t(n){return Array.isArray(n)?n.sort():"object"==typeof n?t(Object.keys(n)).sort(function(t,n){return Number(t)-Number(n)}).map(function(t){return n[t]}):n}(r):t[n]=r,t},Object.create(null))):e}n.extract=u,n.parse=a,n.stringify=function(t,n){!1===(n=o({encode:!0,strict:!0,arrayFormat:"none"},n)).sort&&(n.sort=function(){});var r=function(t){switch(t.arrayFormat){case"index":return function(n,r,e){return null===r?[c(n,t),"[",e,"]"].join(""):[c(n,t),"[",c(e,t),"]=",c(r,t)].join("")};case"bracket":return function(n,r){return null===r?c(n,t):[c(n,t),"[]=",c(r,t)].join("")};default:return function(n,r){return null===r?c(n,t):[c(n,t),"=",c(r,t)].join("")}}}(n);return t?Object.keys(t).sort(n.sort).map(function(e){var o=t[e];if(void 0===o)return"";if(null===o)return c(e,n);if(Array.isArray(o)){var i=[];return o.slice().forEach(function(t){void 0!==t&&i.push(r(e,t,i.length))}),i.join("&")}return c(e,n)+"="+c(o,n)}).filter(function(t){return t.length>0}).join("&"):""},n.parseUrl=function(t,n){return{url:t.split("?")[0]||"",query:a(u(t),n)}}},function(t,n,r){"use strict";var e=r(1),o=r(7),i=r(12),c=r(10),u=r(0);t.exports=function(t,n,r){var a=u(t),f=r(c,a,""[t]),s=f[0],l=f[1];i(function(){var n={};return n[a]=function(){return 7},7!=""[t](n)})&&(o(String.prototype,t,s),e(RegExp.prototype,a,2==n?function(t,n){return l.call(t,this,n)}:function(t){return l.call(t,this)}))}},function(t,n,r){var e=r(11),o=r(2).document,i=e(o)&&e(o.createElement);t.exports=function(t){return i?o.createElement(t):{}}},function(t,n,r){var e=r(9),o=r(2),i=o["__core-js_shared__"]||(o["__core-js_shared__"]={});(t.exports=function(t,n){return i[t]||(i[t]=void 0!==n?n:{})})("versions",[]).push({version:e.version,mode:r(22)?"pure":"global",copyright:"© 2018 Denis Pushkarev (zloirock.ru)"})},function(t,n){t.exports=!1},function(t,n,r){"use strict";var e=r(22),o=r(24),i=r(7),c=r(1),u=r(3),a=r(39),f=r(30),s=r(47),l=r(0)("iterator"),p=!([].keys&&"next"in[].keys()),v=function(){return this};t.exports=function(t,n,r,y,d,h,g){a(r,n,y);var m,x,b,j=function(t){if(!p&&t in _)return _[t];switch(t){case"keys":case"values":return function(){return new r(this,t)}}return function(){return new r(this,t)}},O=n+" Iterator",S="values"==d,w=!1,_=t.prototype,E=_[l]||_["@@iterator"]||d&&_[d],A=E||j(d),L=d?S?j("entries"):A:void 0,k="Array"==n&&_.entries||E;if(k&&(b=s(k.call(new t)))!==Object.prototype&&b.next&&(f(b,O,!0),e||"function"==typeof b[l]||c(b,l,v)),S&&E&&"values"!==E.name&&(w=!0,A=function(){return E.call(this)}),e&&!g||!p&&!w&&_[l]||c(_,l,A),u[n]=A,u[O]=v,d)if(m={values:S?A:j("values"),keys:h?A:j("keys"),entries:L},g)for(x in m)x in _||i(_,x,m[x]);else o(o.P+o.F*(p||w),n,m);return m}},function(t,n,r){var e=r(2),o=r(9),i=r(1),c=r(7),u=r(25),a=function(t,n,r){var f,s,l,p,v=t&a.F,y=t&a.G,d=t&a.S,h=t&a.P,g=t&a.B,m=y?e:d?e[n]||(e[n]={}):(e[n]||{}).prototype,x=y?o:o[n]||(o[n]={}),b=x.prototype||(x.prototype={});for(f in y&&(r=n),r)l=((s=!v&&m&&void 0!==m[f])?m:r)[f],p=g&&s?u(l,e):h&&"function"==typeof l?u(Function.call,l):l,m&&c(m,f,l,t&a.U),x[f]!=l&&i(x,f,p),h&&b[f]!=l&&(b[f]=l)};e.core=o,a.F=1,a.G=2,a.S=4,a.P=8,a.B=16,a.W=32,a.U=64,a.R=128,t.exports=a},function(t,n,r){var e=r(38);t.exports=function(t,n,r){if(e(t),void 0===n)return t;switch(r){case 1:return function(r){return t.call(n,r)};case 2:return function(r,e){return t.call(n,r,e)};case 3:return function(r,e,o){return t.call(n,r,e,o)}}return function(){return t.apply(n,arguments)}}},function(t,n,r){var e=r(42),o=r(29);t.exports=Object.keys||function(t){return e(t,o)}},function(t,n){var r={}.toString;t.exports=function(t){return r.call(t).slice(8,-1)}},function(t,n,r){var e=r(15),o=Math.min;t.exports=function(t){return t>0?o(e(t),9007199254740991):0}},function(t,n){t.exports="constructor,hasOwnProperty,isPrototypeOf,propertyIsEnumerable,toLocaleString,toString,valueOf".split(",")},function(t,n,r){var e=r(4).f,o=r(8),i=r(0)("toStringTag");t.exports=function(t,n,r){t&&!o(t=r?t:t.prototype,i)&&e(t,i,{configurable:!0,value:n})}},function(t,n,r){var e=r(10);t.exports=function(t){return Object(e(t))}},function(t,n,r){"use strict";r.r(n);r(33),r(36),r(48),r(55),r(59);var e=r(18),o=r.n(e);function i(t){"Enter"===t.key&&u()}function c(t){if(t.target){var n=t.target;n.classList.contains("active")?n.classList.remove("active"):n.classList.add("active")}u()}function u(){var t=document.getElementById("avoindata-articles-search-input"),n=[],r=document.querySelectorAll(".avoindata-article-category-filter.active");Array.from(r).forEach(function(t){t.dataset.tagid&&n.push(t.dataset.tagid)});var e=o.a.stringify({search:t.value,"category[]":n});e.length>0?window.location.replace(window.location.origin+"/"+t.dataset.searchLanguage+"/articles?"+e):window.location.replace(window.location.origin+"/"+t.dataset.searchLanguage+"/articles")}document.addEventListener("readystatechange",function(t){if("interactive"===t.target.readyState){!function(){var t=document.getElementById("avoindata-articles-search-btn"),n=document.getElementById("avoindata-articles-search-input");t.onclick=u,n.onkeydown=i}(),function(){var t=document.getElementsByClassName("avoindata-article-category-filter-wrapper");if(t[0]){var n=t[0].querySelectorAll(".avoindata-article-category-filter");Array.from(n).forEach(function(t){t.onclick=c})}}();var n=o.a.parse(location.search),r=[].concat(n.category);r&&Array.from(r).forEach(function(t){var n=document.querySelector('.avoindata-article-category-filter[data-tagid="'.concat(t,'"]'));n&&n.classList.add("active")})}})},function(t,n,r){r(19)("replace",2,function(t,n,r){return[function(e,o){"use strict";var i=t(this),c=void 0==e?void 0:e[n];return void 0!==c?c.call(e,i,o):r.call(String(i),e,o)},r]})},function(t,n,r){t.exports=!r(6)&&!r(12)(function(){return 7!=Object.defineProperty(r(20)("div"),"a",{get:function(){return 7}}).a})},function(t,n,r){var e=r(11);t.exports=function(t,n){if(!e(t))return t;var r,o;if(n&&"function"==typeof(r=t.toString)&&!e(o=r.call(t)))return o;if("function"==typeof(r=t.valueOf)&&!e(o=r.call(t)))return o;if(!n&&"function"==typeof(r=t.toString)&&!e(o=r.call(t)))return o;throw TypeError("Can't convert object to primitive value")}},function(t,n,r){"use strict";var e=r(37)(!0);r(23)(String,"String",function(t){this._t=String(t),this._i=0},function(){var t,n=this._t,r=this._i;return r>=n.length?{value:void 0,done:!0}:(t=e(n,r),this._i+=t.length,{value:t,done:!1})})},function(t,n,r){var e=r(15),o=r(10);t.exports=function(t){return function(n,r){var i,c,u=String(o(n)),a=e(r),f=u.length;return a<0||a>=f?t?"":void 0:(i=u.charCodeAt(a))<55296||i>56319||a+1===f||(c=u.charCodeAt(a+1))<56320||c>57343?t?u.charAt(a):i:t?u.slice(a,a+2):c-56320+(i-55296<<10)+65536}}},function(t,n){t.exports=function(t){if("function"!=typeof t)throw TypeError(t+" is not a function!");return t}},function(t,n,r){"use strict";var e=r(40),o=r(13),i=r(30),c={};r(1)(c,r(0)("iterator"),function(){return this}),t.exports=function(t,n,r){t.prototype=e(c,{next:o(1,r)}),i(t,n+" Iterator")}},function(t,n,r){var e=r(5),o=r(41),i=r(29),c=r(17)("IE_PROTO"),u=function(){},a=function(){var t,n=r(20)("iframe"),e=i.length;for(n.style.display="none",r(46).appendChild(n),n.src="javascript:",(t=n.contentWindow.document).open(),t.write("<script>document.F=Object<\/script>"),t.close(),a=t.F;e--;)delete a.prototype[i[e]];return a()};t.exports=Object.create||function(t,n){var r;return null!==t?(u.prototype=e(t),r=new u,u.prototype=null,r[c]=t):r=a(),void 0===n?r:o(r,n)}},function(t,n,r){var e=r(4),o=r(5),i=r(26);t.exports=r(6)?Object.defineProperties:function(t,n){o(t);for(var r,c=i(n),u=c.length,a=0;u>a;)e.f(t,r=c[a++],n[r]);return t}},function(t,n,r){var e=r(8),o=r(16),i=r(44)(!1),c=r(17)("IE_PROTO");t.exports=function(t,n){var r,u=o(t),a=0,f=[];for(r in u)r!=c&&e(u,r)&&f.push(r);for(;n.length>a;)e(u,r=n[a++])&&(~i(f,r)||f.push(r));return f}},function(t,n,r){var e=r(27);t.exports=Object("z").propertyIsEnumerable(0)?Object:function(t){return"String"==e(t)?t.split(""):Object(t)}},function(t,n,r){var e=r(16),o=r(28),i=r(45);t.exports=function(t){return function(n,r,c){var u,a=e(n),f=o(a.length),s=i(c,f);if(t&&r!=r){for(;f>s;)if((u=a[s++])!=u)return!0}else for(;f>s;s++)if((t||s in a)&&a[s]===r)return t||s||0;return!t&&-1}}},function(t,n,r){var e=r(15),o=Math.max,i=Math.min;t.exports=function(t,n){return(t=e(t))<0?o(t+n,0):i(t,n)}},function(t,n,r){var e=r(2).document;t.exports=e&&e.documentElement},function(t,n,r){var e=r(8),o=r(31),i=r(17)("IE_PROTO"),c=Object.prototype;t.exports=Object.getPrototypeOf||function(t){return t=o(t),e(t,i)?t[i]:"function"==typeof t.constructor&&t instanceof t.constructor?t.constructor.prototype:t instanceof Object?c:null}},function(t,n,r){"use strict";var e=r(25),o=r(24),i=r(31),c=r(49),u=r(50),a=r(28),f=r(51),s=r(52);o(o.S+o.F*!r(54)(function(t){Array.from(t)}),"Array",{from:function(t){var n,r,o,l,p=i(t),v="function"==typeof this?this:Array,y=arguments.length,d=y>1?arguments[1]:void 0,h=void 0!==d,g=0,m=s(p);if(h&&(d=e(d,y>2?arguments[2]:void 0,2)),void 0==m||v==Array&&u(m))for(r=new v(n=a(p.length));n>g;g++)f(r,g,h?d(p[g],g):p[g]);else for(l=m.call(p),r=new v;!(o=l.next()).done;g++)f(r,g,h?c(l,d,[o.value,g],!0):o.value);return r.length=g,r}})},function(t,n,r){var e=r(5);t.exports=function(t,n,r,o){try{return o?n(e(r)[0],r[1]):n(r)}catch(n){var i=t.return;throw void 0!==i&&e(i.call(t)),n}}},function(t,n,r){var e=r(3),o=r(0)("iterator"),i=Array.prototype;t.exports=function(t){return void 0!==t&&(e.Array===t||i[o]===t)}},function(t,n,r){"use strict";var e=r(4),o=r(13);t.exports=function(t,n,r){n in t?e.f(t,n,o(0,r)):t[n]=r}},function(t,n,r){var e=r(53),o=r(0)("iterator"),i=r(3);t.exports=r(9).getIteratorMethod=function(t){if(void 0!=t)return t[o]||t["@@iterator"]||i[e(t)]}},function(t,n,r){var e=r(27),o=r(0)("toStringTag"),i="Arguments"==e(function(){return arguments}());t.exports=function(t){var n,r,c;return void 0===t?"Undefined":null===t?"Null":"string"==typeof(r=function(t,n){try{return t[n]}catch(t){}}(n=Object(t),o))?r:i?e(n):"Object"==(c=e(n))&&"function"==typeof n.callee?"Arguments":c}},function(t,n,r){var e=r(0)("iterator"),o=!1;try{var i=[7][e]();i.return=function(){o=!0},Array.from(i,function(){throw 2})}catch(t){}t.exports=function(t,n){if(!n&&!o)return!1;var r=!1;try{var i=[7],c=i[e]();c.next=function(){return{done:r=!0}},i[e]=function(){return c},t(i)}catch(t){}return r}},function(t,n,r){for(var e=r(56),o=r(26),i=r(7),c=r(2),u=r(1),a=r(3),f=r(0),s=f("iterator"),l=f("toStringTag"),p=a.Array,v={CSSRuleList:!0,CSSStyleDeclaration:!1,CSSValueList:!1,ClientRectList:!1,DOMRectList:!1,DOMStringList:!1,DOMTokenList:!0,DataTransferItemList:!1,FileList:!1,HTMLAllCollection:!1,HTMLCollection:!1,HTMLFormElement:!1,HTMLSelectElement:!1,MediaList:!0,MimeTypeArray:!1,NamedNodeMap:!1,NodeList:!0,PaintRequestList:!1,Plugin:!1,PluginArray:!1,SVGLengthList:!1,SVGNumberList:!1,SVGPathSegList:!1,SVGPointList:!1,SVGStringList:!1,SVGTransformList:!1,SourceBufferList:!1,StyleSheetList:!0,TextTrackCueList:!1,TextTrackList:!1,TouchList:!1},y=o(v),d=0;d<y.length;d++){var h,g=y[d],m=v[g],x=c[g],b=x&&x.prototype;if(b&&(b[s]||u(b,s,p),b[l]||u(b,l,g),a[g]=p,m))for(h in e)b[h]||i(b,h,e[h],!0)}},function(t,n,r){"use strict";var e=r(57),o=r(58),i=r(3),c=r(16);t.exports=r(23)(Array,"Array",function(t,n){this._t=c(t),this._i=0,this._k=n},function(){var t=this._t,n=this._k,r=this._i++;return!t||r>=t.length?(this._t=void 0,o(1)):o(0,"keys"==n?r:"values"==n?t[r]:[r,t[r]])},"values"),i.Arguments=i.Array,e("keys"),e("values"),e("entries")},function(t,n,r){var e=r(0)("unscopables"),o=Array.prototype;void 0==o[e]&&r(1)(o,e,{}),t.exports=function(t){o[e][t]=!0}},function(t,n){t.exports=function(t,n){return{value:n,done:!!t}}},function(t,n,r){r(19)("search",1,function(t,n,r){return[function(r){"use strict";var e=t(this),o=void 0==r?void 0:r[n];return void 0!==o?o.call(r,e):new RegExp(r)[n](String(e))},r]})},function(t,n,r){"use strict";t.exports=function(t){return encodeURIComponent(t).replace(/[!'()*]/g,function(t){return"%"+t.charCodeAt(0).toString(16).toUpperCase()})}},function(t,n,r){"use strict";
/*
object-assign
(c) Sindre Sorhus
@license MIT
*/var e=Object.getOwnPropertySymbols,o=Object.prototype.hasOwnProperty,i=Object.prototype.propertyIsEnumerable;t.exports=function(){try{if(!Object.assign)return!1;var t=new String("abc");if(t[5]="de","5"===Object.getOwnPropertyNames(t)[0])return!1;for(var n={},r=0;r<10;r++)n["_"+String.fromCharCode(r)]=r;if("0123456789"!==Object.getOwnPropertyNames(n).map(function(t){return n[t]}).join(""))return!1;var e={};return"abcdefghijklmnopqrst".split("").forEach(function(t){e[t]=t}),"abcdefghijklmnopqrst"===Object.keys(Object.assign({},e)).join("")}catch(t){return!1}}()?Object.assign:function(t,n){for(var r,c,u=function(t){if(null===t||void 0===t)throw new TypeError("Object.assign cannot be called with null or undefined");return Object(t)}(t),a=1;a<arguments.length;a++){for(var f in r=Object(arguments[a]))o.call(r,f)&&(u[f]=r[f]);if(e){c=e(r);for(var s=0;s<c.length;s++)i.call(r,c[s])&&(u[c[s]]=r[c[s]])}}return u}},function(t,n,r){"use strict";var e=new RegExp("%[a-f0-9]{2}","gi"),o=new RegExp("(%[a-f0-9]{2})+","gi");function i(t,n){try{return decodeURIComponent(t.join(""))}catch(t){}if(1===t.length)return t;n=n||1;var r=t.slice(0,n),e=t.slice(n);return Array.prototype.concat.call([],i(r),i(e))}function c(t){try{return decodeURIComponent(t)}catch(o){for(var n=t.match(e),r=1;r<n.length;r++)n=(t=i(n,r).join("")).match(e);return t}}t.exports=function(t){if("string"!=typeof t)throw new TypeError("Expected `encodedURI` to be of type `string`, got `"+typeof t+"`");try{return t=t.replace(/\+/g," "),decodeURIComponent(t)}catch(n){return function(t){for(var n={"%FE%FF":"��","%FF%FE":"��"},r=o.exec(t);r;){try{n[r[0]]=decodeURIComponent(r[0])}catch(t){var e=c(r[0]);e!==r[0]&&(n[r[0]]=e)}r=o.exec(t)}n["%C2"]="�";for(var i=Object.keys(n),u=0;u<i.length;u++){var a=i[u];t=t.replace(new RegExp(a,"g"),n[a])}return t}(t)}}}]);