(()=>{frappe.provide("press");frappe.provide("press.utils");$.extend(press,{set_hostname_abbreviation:function(e){if(e.doc.hostname){let t=e.doc.hostname.split("-"),r=t[0],n=$.map(t.slice(1),function(a){return a?a.substr(0,1):null}).join("");n?abbr=r+"-"+n:abbr=r,e.set_value("hostname_abbreviation",abbr)}}});})();
//# sourceMappingURL=press.bundle.JRNX644T.js.map
