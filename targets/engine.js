/*
**
** Basic utility functions
**
*/

function clone(a) {
    var constructor, b, proto;
    // Primitive types and functions are flat-out passed by value.
    if (!a || typeof a != "object") {
        return a;
    }
    constructor = a.constructor;
    if (constructor == Date || constructor == RegExp) {
        b = new constructor(a);
    }
    else if (constructor == Array) {
        b = [];
    }
    else if (a.nodeType && typeof a.cloneNode == "function") {
        b = a.cloneNode(true);
    }
    else {
        proto = (typeof Object.getPrototypeOf == "function" ? Object.getPrototypeOf(a) : a.__proto__);
        b = proto ? Object.create(proto) : {};
    }
    // This should work on both arrays and objects equally -
    // even copying expando properties foolishly added to arrays.
    for (var property in a) {
        if (Object.prototype.hasOwnProperty.call(a,property) && !isCyclic(a[property])) {
            if (typeof a[property] == "object") {
                try {
                    b[property] = clone(a[property]);
                    continue;
                }
                catch(e) {}
            }
            b[property] = a[property];
        }
    }
    return b;
}

function isCyclic(obj) {
    var properties = [];
    return (function recurse(obj) {
        var key, i, ownProps = [];
        if (obj && typeof obj == "object") {
            if (properties.indexOf(obj) > -1) {
                return true;
            }
            properties.push(obj);
            for (key in obj) {
                if (Object.prototype.hasOwnProperty.call(obj,key) && recurse(obj[key])) {
                    return true;
                }
            }
        }
        return false;
    }(obj));
}

function insertElement(a, d, f, c, e) {
    var b = document.createElement(d);
    if (f) {
        b.id = f
    }
    if (c) {
        b.className = c
    }
    if (e) {
        insertText(b, e)
    }
    if (a) {
        a.appendChild(b)
    }
    return b
}

function addClickHandler(el, fn) {
    if (el.addEventListener) {
        el.addEventListener('click', fn); 
    } else if (el.attachEvent)  {
        el.attachEvent('onclick', fn);
    }
}

function insertText(a, b) {
    return a.appendChild(document.createTextNode(b))
}

function removeChildren(a) {
    while (a.hasChildNodes()) {
        a.removeChild(a.firstChild)
    }
}

function findPassageParent(el) {
    while(el && el != document.body && !~el.className.indexOf("passage")) {
        el = el.parentNode;
    }
    return el == document.body ? null : el;
}

function setPageElement(c, b, a) {
    var place;
    if (place = (typeof c == "string" ? document.getElementById(c) : c)) {
        removeChildren(place);
        if (tale.has(b)) {
            new Wikifier(place, tale.get(b).processText())
        } else {
            new Wikifier(place, a)
        }
    }
}

var scrollWindowInterval;
function scrollWindowTo(e, margin) {
    var d = window.scrollY ? window.scrollY : document.documentElement.scrollTop,
        m = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight,
        g = k(e),
        j = (d > g) ? -1 : 1,
        b = 0,
        c = Math.abs(d - g);
    scrollWindowInterval && window.clearInterval(scrollWindowInterval);
    if (c) {
        scrollWindowInterval = window.setInterval(h, 25);
    }
    
    function h() {
        b += 0.1;
        window.scrollTo(0, d + j * (c * Math.easeInOut(b)));
        if (b >= 1) {
            window.clearInterval(scrollWindowInterval)
        }
    }

    function k(o) {
        var p = a(o),
            h = o.offsetHeight,
            n = d + m;
        p = Math.min(Math.max(p + (margin || 0) * ( p < d ? -1 : 1), 0), n);
        if (p < d) {
            return p
        } else {
            if (p+h > n) {
                if (h < m) {
                    return (p - (m - h) + 20)
                } else {
                    return p
                }
            } else {
                return p
            }
        }
    }

    function a(l) {
        var m = 0;
        while (l.offsetParent) {
            m += l.offsetTop;
            l = l.offsetParent
        }
        return m
    }
}

// Returns an object containing the properties in neu which differ from old.
function delta(old,neu) {
    var vars, ret = {};
    if (old && neu) {
        for (vars in neu) {
            if (neu[vars] !== old[vars]) {
                ret[vars] = neu[vars];
            }
        }
    }
    return ret;
}

// Convert various exotic objects into JSON-serialisable plain objects.
function decompile(val) {
    var i, ret;
    if ((typeof val != "object" && typeof val != "function") || !val) {
        return val;
    }
    // Passage objects: store only their name
    else if (val instanceof Passage) {
        return { "[[Passage]]" : val.id };
    }
    else if (Array.isArray(val)) {
        ret = [];
    }
    else {
        ret = {};
    }
    // Deep-copy own properties
    for (i in val) {
        if (Object.prototype.hasOwnProperty.call(val,i) && !isCyclic(val[i])) {
            ret[i] = decompile(val[i]);
        }
    }
    // Functions: store the decompiled function body as a property
    // arbitrarily called "[[Call]]".
    if (typeof val == "function" || val instanceof RegExp) {
        try {
            // Check if it can be recompiled (i.e. isn't a bound or native)
            internalEval(val+"");
            ret["[[Call]]"] = val+"";
        } catch(e) {
            // Silently fail
            ret["[[Call]]"] = "function(){}"
        }
    }
    return ret;
}

// Reverses the effects of decompile()
// Takes recently JSON.parse()d objects and makes them exotic again.
function recompile(val) {
    var i, ret = val;
    if (val && typeof val == "object") {
        // Passages
        if (typeof val["[[Passage]]"] == "number") {
            return tale.get(val["[[Passage]]"]);
        }
        // Functions/RegExps
        if (typeof val["[[Call]]"] == "string") {
            try {
                ret = internalEval(val["[[Call]]"]);
            }
            catch(e){}
        }
        // Recursively recompile all properties
        // or, if a function/regexp, deep-copy them to the new function.
        for (i in val) {
            if (Object.prototype.hasOwnProperty.call(val,i)) {
                ret[i] = recompile(val[i]);
            }
        }
    }
    return ret;
}

function addStyle(b) {
    if (document.createStyleSheet) {
        document.getElementsByTagName("head")[0].insertAdjacentHTML("beforeEnd", "&nbsp;<style>" + b + "</style>")
    } else {
        var a = document.createElement("style");
        a.appendChild(document.createTextNode(b));
        document.getElementsByTagName("head")[0].appendChild(a)
    }
}

function alterCSS(text) {
    var temp = '', imgPassages = tale.lookup("tags", "Twine.image");
    // Remove comments
    text = text.replace(/\/\*(?:[^\*]|\*(?!\/))*\*\//g,'');
    // Replace :link
    text = text.replace(/:link/g,"[class*=Link]");
    // Replace :visited
    text = text.replace(/:visited/g,".visitedLink");
    // Hoist @import
    text = text.replace(/@import\s+(?:url\s*\(\s*['"]?|['"])[^"'\s]+(?:['"]?\s*\)|['"])\s*([\w\s\(\)\d\:,\-]*);/g, function(e) {
        temp += e; return '';
    });
    text = temp + text;
    
    // Add images
    return text.replace(new RegExp(Wikifier.imageFormatter.lookahead, "gim"), function(m,p1,p2,p3,src) {
        for (var i = 0; i < imgPassages.length; i++) {
            if (imgPassages[i].title == src) {
                src = imgPassages[i].text;
                break;
            }
        }
        return "url(" + src + ")"
    });
}

function setTransitionCSS(styleText) {
    styleText = alterCSS(styleText);
    var style = document.getElementById("transitionCSS");
    style.styleSheet ? (style.styleSheet.cssText = styleText) : (style.innerHTML = styleText);
}

function throwError(a, b, tooltip) {
    if (a) {
        var elem = insertElement(a, "span", null, "marked", b);
        tooltip && elem.setAttribute("title", tooltip);
    } else {
        alert("Regrettably, this " + tale.identity() + "'s code just ran into a problem:\n" + b + ".\n"+softErrorMessage);
    }
}
Math.easeInOut = function (a) {
    return (1 - ((Math.cos(a * Math.PI) + 1) / 2))
};
String.prototype.readMacroParams = function (keepquotes) {
    var exec, re = /(?:\s*)(?:(?:"([^"]*)")|(?:'([^']*)')|(?:\[\[((?:[^\]]|\](?!\]))*)\]\])|([^"'\s]\S*))/mg,
        params = [];
    do {
        var val;
        exec = re.exec(this);
        if (exec) {
            if (exec[1]) {
                val = exec[1];
                keepquotes && (val = '"' + val + '"');
            } else if (exec[2]) {
                val = exec[2];
                keepquotes && (val = "'" + val + "'");
            } else if (exec[3]) {
                val = exec[3];
                keepquotes && (val = '"' + val.replace('"','\\"') + '"');
            } else if (exec[4]) {
                val = exec[4];
            }
            val && params.push(val);
        }
    } while (exec);
    return params
};
String.prototype.readBracketedList = function () {
    var c, b = "\\[\\[([^\\]]+)\\]\\]",
        a = "[^\\s$]+",
        e = "(?:" + b + ")|(" + a + ")",
        d = new RegExp(e, "mg"),
        f = [];
    do {
        c = d.exec(this);
        if (c) {
            if (c[1]) {
                f.push(c[1])
            } else {
                if (c[2]) {
                    f.push(c[2])
                }
            }
        }
    } while (c);
    return (f)
};

function rot13(s) {
  return s.replace(/[a-zA-Z]/g, function(c) {
    return String.fromCharCode((c<="Z" ? 90 : 122) >= (c=c.charCodeAt()+13) ? c : c-26);
  });
}

/*
**
** Polyfills
**
*/

Object.create || (function() {
    var F = function(){};
    Object.create = function (o) {
        if (typeof o != 'object') throw TypeError();
        F.prototype = o;
        return new F();
    };
})();
String.prototype.trim || (String.prototype.trim = function () {
    return this.replace(/^\s\s*/, "").replace(/\s\s*$/, "")
});
Array.isArray || (Array.isArray = function(arg) {
    return Object.prototype.toString.call(arg) === '[object Array]';
});
Array.prototype.indexOf || (Array.prototype.indexOf = function (b, d) {
    d = (d == null) ? 0 : d;
    var a = this.length;
    for (var c = d; c < a; c++) {
        if (this[c] == b) {
            return c
        }
    }
    return -1
});
Array.prototype.forEach || (Array.prototype.forEach=function(fun){if(this==null){throw TypeError()}var t=Object(this);var len=+t.length;if(typeof fun!="function"){throw TypeError()}var thisArg=arguments.length>=2?arguments[1]:void 0;for(var i=0;i<len;i++){if(i in t){fun.call(thisArg,t[i],i,t)}}});

/* btoa/atob polyfill by github.com/davidchambers */
(function(){function t(t){this.message=t}var e=window,r="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";t.prototype=Error(),t.prototype.name="InvalidCharacterError",e.btoa||(e.btoa=function(e){for(var o,n,a=0,i=r,c="";e.charAt(0|a)||(i="=",a%1);c+=i.charAt(63&o>>8-8*(a%1))){if(n=e.charCodeAt(a+=.75),n>255)throw new t();o=o<<8|n}return c}),e.atob||(e.atob=function(e){if(e=e.replace(/=+$/,""),1==e.length%4)throw new t();for(var o,n,a=0,i=0,c="";n=e.charAt(i++);~n&&(o=a%4?64*o+n:n,a++%4)?c+=String.fromCharCode(255&o>>(6&-2*a)):0)n=r.indexOf(n);return c})})();

/* Polyfill for fade transition */
var hasTransition = 'transition' in document.documentElement.style || '-webkit-transition' in document.documentElement.style;

function fade(f, c) {
    var h;
    var e = f.cloneNode(true);
    var g = (c.fade == "in") ? 1 : -1;
    f.parentNode.replaceChild(e, f);
    if (c.fade == "in") {
        h = 0;
        e.style.visibility = "visible"
    } else {
        h = 1
    }
    b(e, h);
    var a = window.setInterval(d, 25);

    function d() {
        h += 0.05 * g;
        b(e, Math.easeInOut(h));
        if (((g == 1) && (h >= 1)) || ((g == -1) && (h <= 0))) {
            f.style.visibility = (c.fade == "in") ? "visible" : "hidden";
            if (e.parentNode) {
                e.parentNode.replaceChild(f, e);
            }
            window.clearInterval(a);
            if (c.onComplete) {
                c.onComplete.call(f)
            }
        }
    }

    function b(k, j) {
        var l = Math.floor(j * 100);
        k.style.zoom = 1;
        k.style.filter = "alpha(opacity=" + l + ")";
        k.style.opacity = j
    }
}

/*
**
** History object
**
*/

function History() {
    this.history = [{
        passage: null,
        variables: {}
    }]
    // Unique identifier for this game session
    this.id = new Date().getTime()+'';
    // URL of the bookmark link
    this.hash = '';
}

History.prototype.encodeHistory = function(b, noVars) {
    var ret = ".", vars, type, hist = this.history[b],
        d = this.history[b+1] ? delta(this.history[b+1].variables, hist.variables) : hist.variables;
    
    function vtob(val) {
        try {
            return window.btoa(unescape(encodeURIComponent(JSON.stringify(decompile(val)))));
        } catch(e) {
            return "0";
        }
    }
    
    if (!hist.passage || hist.passage.id == null) {
        return ""
    }
    ret += hist.passage.id.toString(36);
    if (noVars) {
        return ret;
    }
    for (vars in d) {
        type = typeof d[vars];
        if (type != "undefined") {
            ret += "$" + vtob(vars) + "," + vtob(d[vars]);
        }
    }
    for (vars in hist.linkVars) {
        type = typeof hist.linkVars[vars];
        if (type != "function" && type != "undefined") {
            ret += "[" + vtob(vars) + "," + vtob(hist.linkVars[vars]);
        }
    }
    return ret
};

History.decodeHistory = function(str, prev) {
    var name, splits, variable, c, d,
        ret = { variables: clone(prev.variables) || {} },
        match = /([a-z0-9]+)((?:\$[A-Za-z0-9\+\/=]+,[A-Za-z0-9\+\/=]+)*)((?:\[[A-Za-z0-9\+\/=]+,[A-Za-z0-9\+\/=]+)*)/g.exec(str);
    
    function btov(str) {
        try {
            return recompile(JSON.parse(decodeURIComponent(escape(window.atob(str)))));
        } catch(e) {
            return 0;
        }
    }
    if (match) {
        name = parseInt(match[1], 36);
        if (!tale.has(name)) {
            return false
        }
        if (match[2]) {
            ret.variables || (ret.variables = {});
            splits = match[2].split('$');
            for (c = 0; c < splits.length; c++) {
                variable = splits[c].split(",");
                d = btov(variable[0]);
                if (d) {
                    ret.variables[d]=btov(variable[1]);
                }
            }
        }
        if (match[3]) {
            ret.linkVars || (ret.linkVars = {});
            splits = match[3].split('[');
            for (c = 0; c < splits.length; c++) {
                variable = splits[c].split(",");
                d = btov(variable[0]);
                if (d) {
                    ret.linkVars[d]=btov(variable[1]);
                }
            }
        }
        ret.passage = tale.get(name);
        return ret;
    }
};

History.prototype.save = function() {
    var hist, b, a = "";

    for (b = this.history.length - 1; b >= 0; b--) {
        hist = this.history[b];
        if (!hist) {
            break;
        }
        a += this.encodeHistory(b);
    }
    return "#" + a
};

History.prototype.restore = function () {
    var a, b, c, vars;

    try {
        if (!window.location.hash || (window.location.hash == "#")) {
            if (testplay) {
                if (tale.has("StoryInit")) {
                    new Wikifier(insertElement(null, "span"), tale.get("StoryInit").text);
                }
                this.display(testplay, null, 'quietly');
                return true
            }
            return false
        }
        if (window.location.hash.substr(0, 2) == '#!') {
            c = window.location.hash.substr(2).split('_').join(' ');
            this.display(c, null, 'quietly');
            return true
        }
        a = window.location.hash.replace("#", "").split(".");
        for (b = 0; b < a.length; b++) {
            vars = History.decodeHistory(a[b], vars || {});
            if (vars) {
                if (b == a.length - 1) {
                    vars.variables = clone(this.history[0].variables);
                    for (c in this.history[0].linkVars) {
                        vars.variables[c] = clone(this.history[0].linkVars[c]);
                    }
                    this.history.unshift(vars);
                    this.display(vars.passage.title, null, "back");
                }
                else {
                    this.history.unshift(vars);
                }
            }
        }
        return true
    } catch (d) {
        return false
    }
};

History.prototype.saveVariables = function(c, el, callback) {

    if (typeof callback == "function") {
        callback.call(el);
    }

    this.history.unshift({
        passage: c,
        variables: clone(this.history[0].variables)
    });
};
var restart = History.prototype.restart = function () {
    if (typeof window.history.replaceState == "function") {
        (typeof this.pushState == "function") && this.pushState(true, window.location.href.replace(/#.*$/,''));
        window.location.reload()
    }
    else {
        window.location.hash = "";
    }
};

/*
**
** Macros
**
*/

var version = {
    major: 4,
    minor: 3,
    revision: 0,
    date: new Date("2014"),
    extensions: {}
};
var testplay, tale, state, prerender = {}, postrender = {}, macros = window.macros = {};

version.extensions.displayMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.display = {
    // Used by parameter() and parameterValue()
    parameters: [],
    handler: function (place, macroName, params, parser) {
        var t, j, output, oldDisplayParams, name = parser.fullArgs();
        
        if (macroName != "display") {
            output = macroName;
            // Shorthand displays can have parameters
            params = parser.fullMatch().replace(/^\S*|>>$/g,'').readMacroParams(true);
            // The above line recreates params, with the quotes.
            try {
                for(j=0; j < params.length; j++) {
                    params[j] = internalEval(Wikifier.parse(params[j]));
                }
            } catch (e) {
                throwError(place, parser.fullMatch() + " bad argument: " + params[j], parser.fullMatch());
                return
            }
        }
        else {
            try {
                output = internalEval(name);
            }
            catch(e) {
            }
            if (output == null) {
                // Last-ditch attempt
                if (tale.has(name)) {
                    output = name;
                }
            }
        }
        if (!output) {
            throwError(place, '<<' + macroName + '>>: "' +name + "\" did not evaluate to a passage name", parser.fullMatch());
        } else if (!tale.has(output+"")) {
            throwError(place, '<<' + macroName + ">>: The \"" + output + "\" passage does not exist", parser.fullMatch());
        } else {
            oldDisplayParams = this.parameters;
            this.parameters = params;
            t = tale.get(output+"");
            if (t.tags.indexOf("script") > -1) {
                scriptEval(t);
            }
            else {
                new Wikifier(place, t.processText());
            }
            this.parameters = oldDisplayParams; 
        }
    }
};

version.extensions.actionsMacro = {
    major: 1,
    minor: 2,
    revision: 0
};
macros.actions = {
    handler: function (a, f, g) {
        var v = state.history[0].variables, e = insertElement(a, "ul");
        if (!v["actions clicked"]) {
            v["actions clicked"] = {}
        }
        for (var b = 0; b < g.length; b++) {
            if (v["actions clicked"][g[b]]) {
                continue
            }
            var d = insertElement(e, "li");
            var c = Wikifier.createInternalLink(d, g[b], (function(link) {
                return function() { state.history[0].variables["actions clicked"][link] = true; }
            }(g[b])));
            insertText(c, g[b]);
        }
    }
};
version.extensions.printMacro = {
    major: 1,
    minor: 1,
    revision: 1
};
macros.print = {
    handler: function (place, macroName, params, parser) {
        var args = parser.fullArgs(macroName != "print"), output;
        try {
            // See comment within macros.display
            output = internalEval(args);
            if (output != null && (typeof output != "number" || !isNaN(output))) {
                new Wikifier(place, ''+output);
            }
        } catch (e) {
            throwError(place, "<<print>> bad expression: " + params.join(' '), parser.fullMatch());
        }
    }
};
version.extensions.setMacro = {
    major: 1,
    minor: 1,
    revision: 0
};
macros.set = {
    handler: function (a, b, c, parser) {
        macros.set.run(a, parser.fullArgs(), parser, c.join(' '))
    },
    run: function (a,expression, parser, original) {
        try {
            return internalEval(expression);
        } catch (e) {
            throwError(a, "bad expression: " + (original || expression), parser ? parser.fullMatch() : expression)
        }
    }
};
version.extensions.ifMacros = {
    major: 2,
    minor: 0,
    revision: 0
};
macros["if"] = {
    handler: function (place, macroName, params, parser) {
        var conditions = [],
            clauses = [],
            rawConds = [],
            srcOffset = parser.source.indexOf(">>", parser.matchStart) + 2,
            src = parser.source.slice(srcOffset),
            endPos = -1,
            rawCond = params.join(' '),
            currentCond = parser.fullArgs(),
            currentClause = "",
            t = 0,
            nesting = 0,
            i = 0;
        
        for (; i < src.length; i++) {
            if ((src.substr(i, 6) == "<<else") && !nesting) {
                rawConds.push(rawCond);
                conditions.push(currentCond.trim());
                clauses.push(currentClause);
                currentClause="";
                t = src.indexOf(">>",i+6);
                if(src.substr(i+6,4)==" if " || src.substr(i+6,3)=="if ") {
                    rawCond = src.slice(i+9,t);
                    currentCond = Wikifier.parse(rawCond);
                }
                else {
                    rawCond = "";
                    currentCond = "true";
                }
                i = t+2;
            }
            if (src.substr(i, 5) == "<<if ") {
                nesting++;
            }
            if (src.substr(i, 9) == "<<endif>>") {
                nesting--;
                if (nesting < 0) {
                    endPos = srcOffset + i + 9;
                    rawConds.push(rawCond);
                    conditions.push(currentCond.trim());
                    clauses.push(currentClause);
                    break;
                }
            }
            currentClause += src.charAt(i);
        }

        if (endPos != -1) {
            parser.nextMatch = endPos;
            try {
                for(i=0;i<clauses.length;i++) {
                    if (internalEval(conditions[i])) {
                        new Wikifier(place, clauses[i]);
                        break;
                    }
                }
            } catch (e) {
                throwError(place, "<<" + (i ? "else " : "") + "if>> bad condition: " + rawConds[i], !i ? parser.fullMatch()
                    : "<<else if " + rawConds[i] + ">>");
            }
        } else {
            throwError(place, "I can't find a matching <<endif>>", parser.fullMatch());
        }
    }
};
macros["else"] = macros.elseif = macros.endif = {
    handler: function () {}
};

version.extensions.rememberMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.remember = {
    handler: function (place, macroName, params, parser) {
        var variable, value, re, match,
            statement = params.join(" ");
        macros.set.run(place, parser.fullArgs(), null, params.join(' '));
        if (!window.localStorage) {
            throwError(place, "<<remember>> can't be used "
                + (window.location.protocol == "file:" ? " by local HTML files " : "") + " in this browser.",parser.fullMatch());
            return;
        }
        re = new RegExp(Wikifier.textPrimitives.variable, "g");
        while (match = re.exec(statement)) {
            variable = match[1];
            value = state.history[0].variables[variable];
            try {
                value = JSON.stringify(value);
            } catch (e) {
                throwError(place, "can't <<remember>> the variable $" + variable + " (" + (typeof value) + ")", parser.fullMatch());
                return;
            }
            window.localStorage[this.prefix + variable] = value;
        }
    },
    init: function () {
        var i, variable, value;
        this.prefix = "Twine." + tale.defaultTitle + ".";
        for (i in window.localStorage) {
            if (i.indexOf(this.prefix) == 0) {
                variable = i.substr(this.prefix.length);
                value = window.localStorage[i];
                try {
                    value = JSON.parse(value);
                    state.history[0].variables[variable]=value;
                } catch (e) {
                }
            }
        }
    },
    expire: null,
    prefix: null
};

version.extensions.forgetMacro = {
    major: 1,
    minor: 0,
    revision: 0
};
macros.forget = {
    handler: function (place, macroName, params) {
        var re, match, variable,
            statement = params.join(" ");
        re = new RegExp(Wikifier.textPrimitives.variable, "g");
        while (match = re.exec(statement)) {
            variable = match[1] + ""
            delete state.history[0].variables[variable];
            delete window.localStorage[macros.remember.prefix + variable];
        }
    }
};
            
version.extensions.SilentlyMacro = {
    major: 1,
    minor: 1,
    revision: 0
};
macros.nobr = macros.silently = {
    handler: function (place, macroName, f, parser) {
        var i, h = insertElement(null, 'div'),
            k = parser.source.indexOf('>>', parser.matchStart) + 2,
            a = parser.source.slice(k),
            d = -1,
            c = '',
            l = 0;
        for (i = 0; i < a.length; i++) {
            if (a.substr(i, macroName.length+7) == '<<end' + macroName + '>>') {
                if (l == 0) {
                    d = k + i + macroName.length+7;
                    break;
                } else {
                    l--;
                }
            } else if (a.substr(i, macroName.length+4) == '<<' + macroName + '>>') {
                l++;
            }
            if (macroName == "nobr" && a.charAt(i) == '\n') {
                c += "\u200c"; // Zero-width space
            }
            else {
                c += a.charAt(i);
            }
        }
        if (d != -1) {
            new Wikifier(macroName == "nobr" ? place : h, c);
            parser.nextMatch = d;
        } else {
            throwError(place, "can't find matching <<end" + macroName+">>", parser.fullMatch());
        }
    }
};
macros.endsilently = {
    handler: function () {}
};

version.extensions.choiceMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.choice = {
    callback: function() {
        var i, other, passage = findPassageParent(this);
        
        if (passage) {
            other = passage.querySelectorAll(".choice");
            for (i = 0; i < other.length; i++) {
                other[i].outerHTML = "<span class=disabled>" + other[i].innerHTML + "</span>";
            }
            state.history[0].variables["choice clicked"][passage.id.replace(/\|[^\]]*$/,'')] = true;
        }
    },
    handler: function (A, C, D, parser) {
        var link, id, match,
            text = D[1] || D[0].split("|")[0],
            passage = findPassageParent(A);
        // Get ID of the "choice clicked" entry
        if (!passage) {
            throwError(A, "<<"+C+">> can't be used here.",parser.fullMatch());
            return;
        }
        id = (passage && passage.id.replace(/\|[^\]]*$/,''));
        if (id && (state.history[0].variables["choice clicked"] || 
                (state.history[0].variables["choice clicked"] = {}))[id]) {
            insertElement(A, "span", null, "disabled", text); 
        }
        else {
            match = new RegExp(Wikifier.linkFormatter.lookahead).exec(parser.fullMatch());
            
            if (match) {
                link = Wikifier.linkFormatter.makeLink(A,match,this.callback);
            }
            else {
                link = Wikifier.linkFormatter.makeLink(A,[0,text,D[0]],this.callback);
            }
            link.className += " " + C;
        }
    }
};

version.extensions.backMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.back = {
    labeltext: '&#171; back',
    handler: function (a, b, e, parser) {
        var labelParam, c, el,
            labeltouse = this.labeltext,
            steps = 1,
            stepsParam = e.indexOf("steps"),
            stepsParam2 = "";
        // Steps parameter
        if(stepsParam > 0) {
            stepsParam2 = e[stepsParam - 1];
            if(stepsParam2[0] == '$') {
                try {
                    stepsParam2 = internalEval(Wikifier.parse(stepsParam2));
                }
                catch(r) {
                    throwError(a, parser.fullMatch() + " bad expression: " + r.message, parser.fullMatch())
                    return;
                }
            }
            // Previously, trying to go back more steps than were present in the
            // history would silently revert to just 1 step. 
            // Instead, let's just go back to the start.
            steps = +stepsParam2;
            if(steps >= state.history.length - 1) {
                steps = state.history.length - 2;
            }
            e.splice(stepsParam - 1, 2);
        }
        // Label parameter
        labelParam = e.indexOf("label");
        if(labelParam > -1) {
            if(!e[labelParam + 1]) {
                throwError(a, parser.fullMatch() + ": " + e[labelParam] + ' keyword needs an additional label parameter', parser.fullMatch());
                return;
            }
            labeltouse = e[labelParam + 1];
            e.splice(labelParam, 2);
        }
        // What's left is the passage name parameter
        if(stepsParam <= 0) {
            if(e[0]) {
                if(e[0].charAt(0) == '$') {
                    try {
                        e = internalEval(Wikifier.parse(e[0]));
                    }
                    catch(r) {
                        throwError(a, parser.fullMatch() + " bad expression: " + r.message, parser.fullMatch())
                        return;
                    }
                }
                else {
                    e = e[0];
                }
                if(!tale.has(e)) {
                    throwError(a, "The \"" + e + "\" passage does not exist",parser.fullMatch());
                    return;
                }
                for(c = 0; c < state.history.length; c++) {
                    if(state.history[c].passage.title == e) {
                        steps = c;
                        break;
                    }
                }
            }
        }
        el = document.createElement("a");
        el.className = b;
        addClickHandler(el, (function(b) { return function () {
            return macros.back.onclick(b == "back", steps, el)
        }}(b)));
        el.innerHTML = labeltouse;
        a.appendChild(el);
    }
};

version.extensions.returnMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros["return"] = {
  labeltext: '&#171; return',
  handler: function(a,b,e) { 
    macros.back.handler.call(this,a,b,e);
  }
};

version.extensions.textInputMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.checkbox = macros.radio = macros.textinput = {
    handler: function (A, C, D, parser) {
        var match,
            class_ = C.replace('input','Input'),
            q = A.querySelectorAll('input'),
            id = class_ + "|" + ((q && q.length) || 0);
            input = insertElement(null, 'input', id, class_);
        
        input.name=D[0];
        input.type=C.replace('input','');
        // IE 8 support - delay insertion until now
        A.appendChild(input);
        
        if (C == "textinput" && D[1]) {
            match = new RegExp(Wikifier.linkFormatter.lookahead).exec(parser.fullMatch());
            
            if (match) {
                Wikifier.linkFormatter.makeLink(A,match, macros.button.callback, 'button');
            }
            else {
                Wikifier.linkFormatter.makeLink(A,[0,(D[2] || D[1]),D[1]], macros.button.callback, 'button');
            }
        }
        else if ((C == "radio" || C == "checkbox") && D[1]) {
            input.value = D[1];
            insertElement(A, 'label','', '', D[1]).setAttribute('for',id);
            if (D[2]) {
                insertElement(A,'br');
                D.splice(1,1);
                macros[C].handler(A,C,D)
            }
        }
    }
};

version.extensions.buttonMacro = {
    major: 1,
    minor: 0,
    revision: 0
};
macros.button = {
    callback: function() {
        var el = findPassageParent(this);
        if (el) {
            var inputs = el.querySelectorAll("input");
            for (i = 0; i < inputs.length; i++) {
                if (inputs[i].type!="checkbox" && (inputs[i].type!="radio" || inputs[i].checked)) {
                    macros.set.run(null, Wikifier.parse(inputs[i].name+' = "'+inputs[i].value.replace(/"/g,'\\"')+'"'));
                }
                else if (inputs[i].type=="checkbox" && inputs[i].checked) {
                    macros.set.run(null, Wikifier.parse(
                        inputs[i].name+' = [].concat('+inputs[i].name+' || []);'));
                    macros.set.run(null, Wikifier.parse(
                        inputs[i].name+'.push("'+inputs[i].value.replace(/"/g,'\\"')+'")'));
                }
            }
        }
    },
    handler: function (A, C, D, parser) {
        var link,
            match = new RegExp(Wikifier.linkFormatter.lookahead).exec(parser.fullMatch());
        
        if (match) {
            Wikifier.linkFormatter.makeLink(A, match, this.callback, 'button');
        }
        else {
            Wikifier.linkFormatter.makeLink(A,[0,D[1] || D[0], D[0]], this.callback, 'button');
        }
    }
};

/*
**
** Passage object
**
*/

function Passage(c, b, a, ofunc) {
    var t;
    if (!this || this.constructor != Passage) {
        throw new ReferenceError("passage() must be in lowercase");
    }
    this.title = c;
    ofunc = typeof ofunc == 'function' && ofunc;
    if (b) {
        this.id = a;
        // Load tags
        this.tags = b.getAttribute("tags");
        if (typeof this.tags == "string") {
            if (ofunc) {
                this.tags = ofunc(this.tags);
            }
            this.tags = this.tags.readBracketedList();
        } else this.tags = [];
        // Load text
        t = b.firstChild ? b.firstChild.nodeValue : "";
        if (ofunc && !this.isImage()) {
            this.text = ofunc(Passage.unescapeLineBreaks(t));
        } else {
            this.text = Passage.unescapeLineBreaks(t);
        }
        // Preload linked images
        if (!this.isImage()) {
            this.preloadImages();
        }
        // Check for the .char selector, or the [data-char] selector
        // False positives aren't a big issue.
        if (/\.char\b|\[data\-char\b/.exec(this.text) && Wikifier.charSpanFormatter) {
            Wikifier.formatters.push(Wikifier.charSpanFormatter);
            delete Wikifier.charSpanFormatter;
        }
    } else {
        this.text = '@@This passage does not exist: ' + c + '@@';
        this.tags = [];
    }
}
Passage.prototype.isImage = function() {
    return !!~(this.tags.indexOf("Twine.image"));
};
Passage.prototype.preloadImages = function() {
    // Don't preload URLs containing '$' - suspect that they are variables.
    var u = "\\s*['\"]?([^\"'$]+\\.(jpe?g|a?png|gif|bmp|webp|svg))['\"]?\\s*",
        k = function(c, e) {
            var i,d;
            do {
                d = c.exec(this.text);
                if(d) {
                    i = new Image();
                    i.src = d[e];
                }
            } while (d);
            return k;
        };
    k.call(this, new RegExp(Wikifier.imageFormatter.lookahead.replace("[^\\[\\]\\|]+",u), "mg"), 4)
        .call(this, new RegExp("url\\s*\\(" + u + "\\)", "mig"), 1)
        .call(this, new RegExp("src\\s*=" + u, "mig"), 1);
};

Passage.unescapeLineBreaks = function (a) {
    if (a && typeof a == "string") {
        return a.replace(/\\n/mg, "\n").replace(/\\t/mg, "\t").replace(/\\s/mg, "\\").replace(/\\/mg, "\\").replace(/\r/mg, "")
    } else {
        return ""
    }
};
Passage.prototype.setTags = function(b) {
    var t = this.tags != null && this.tags.length ? this.tags.join(' ') : "";
    if (t) {
        b.setAttribute('data-tags', this.tags.join(' '));
    }
    document.body.setAttribute("data-tags", t);
};
Passage.prototype.processText = function() {
    var ret = this.text;
    if (~this.tags.indexOf("nobr")) {
        ret = ret.replace(/\n/g,"\u200c");
    }
    if (this.isImage()) {
        ret = "[img[" + ret + "]]"
    }
    return ret;
};

/*
**
** Tale object
**
*/

function Tale() {
    var a,b,c,lines,i,kv,nsc,isImage,
        settings = this.storysettings = {
            lookup: function(a, dfault) {
                // The two runtime settings (undo and bookmark) default to true.
                if (!(a in this)) return dfault;
                return (this[a]+"") != "off";
            }
        },
        HTMLtitle = document.querySelector('title');
        tiddlerTitle = '';
    this.defaultTitle = (HTMLtitle && (HTMLtitle.textContent || HTMLtitle.innerText)) || "Untitled Story";
    this.passages = {};
    //Look for and load the StorySettings
    if (document.normalize) document.normalize();
    a = document.getElementById("storeArea").children;
    for (b = 0; b < a.length; b++) {
        c = a[b];
        if (c.getAttribute && c.getAttribute("tiddler") == 'StorySettings') {
            lines = new Passage('StorySettings', c, 0, null, null).text.split('\n');
            for (i in lines) {
                if (typeof lines[i] == "string" && lines[i].indexOf(':') > -1) {
                    kv = lines[i].toLowerCase().split(':');
                    kv[0] = kv[0].replace(/^\s+|\s+$/g, '');
                    kv[1] = kv[1].replace(/^\s+|\s+$/g, '');
                    if (kv[0] != "lookup") {
                        settings[kv[0]] = kv[1];
                    }
                }
            }
        }
    }
    //Load in the passages
    if (settings.obfuscate == 'rot13') {
        for (b = 0; b < a.length; b++) {
            c = a[b];
            if (c.getAttribute && (tiddlerTitle = c.getAttribute("tiddler"))) {
                isImage = (c.getAttribute("tags")+"").indexOf("Twine.image")>-1;
                if (tiddlerTitle != 'StorySettings' && !isImage) 
                    tiddlerTitle = rot13(tiddlerTitle);
                this.passages[tiddlerTitle] = new Passage(tiddlerTitle, c, b+1, !isImage && rot13);
            }
        }
    } else {
        for (b = 0; b < a.length; b++) {
            c = a[b];
            if (c.getAttribute && (tiddlerTitle = c.getAttribute("tiddler"))) {
                this.passages[tiddlerTitle] = new Passage(tiddlerTitle, c, b, null, null)
            }
        }
    }
}
Tale.prototype.has = function (a) {
    if (typeof a == "string") {
        return (this.passages[a] != null)
    } else {
        for (var i in this.passages) {
            if (this.passages[i].id == a) {
                return true
            }
        }
        return false
    }
};
Tale.prototype.get = function (a) {
    if (typeof a == "string") {
        return this.passages[a] || new Passage(a)
    } else {
        for (var i in this.passages) {
            if (this.passages[i].id == a) {
                return this.passages[i]
            }
        }
    }
};
Tale.prototype.lookup = function (h, g, a) {
    var d = [];
    for (var c in this.passages) {
        var f = this.passages[c];
        for (var b = 0; b < f[h].length; b++) {
            if (f[h][b] == g) {
                d.push(f)
            }
        }
    }
    if (!a) {
        a = "title"
    }
    d.sort(function (k, j) {
        if (k[a] == j[a]) {
            return (0)
        } else {
            return (k[a] < j[a]) ? -1 : +1
        }
    });
    return d
};
Tale.prototype.canUndo = function() {
    return this.storysettings.lookup('undo',true);
};
Tale.prototype.identity = function () {
    var meta = document.querySelector("meta[name='identity']"),
        identity = meta ? meta.getAttribute("content") : "story";
    
    return (Tale.prototype.identity = function() {
        return identity;
    })();
};
Tale.prototype.forEachStylesheet = function(tags, callback) {
    var passage, i;
    tags = tags || [];
    
    if (typeof callback != "function")
        return;
    for (passage in this.passages) {
        passage = tale.passages[passage];
        if (passage && ~passage.tags.indexOf("stylesheet")) {
            for (i = 0; i < tags.length; i++) {
                if (~passage.tags.indexOf(tags[i])) {
                    callback(passage);
                    break;
                }
            }
        }
    }
};
Tale.prototype.setPageElements = function() {
    var storyTitle;
    
    setPageElement("storyTitle", "StoryTitle", this.defaultTitle);
    storyTitle = document.getElementById("storyTitle");
    document.title = this.title = (storyTitle && (storyTitle.textContent || storyTitle.innerText)) || this.defaultTitle;
    
    setPageElement("storySubtitle", "StorySubtitle", "");
    if (tale.has("StoryAuthor")) {
        setPageElement("titleSeparator", null, "\n");
        setPageElement("storyAuthor", "StoryAuthor", "");
    }
    if (tale.has("StoryMenu")) {
        document.getElementById("storyMenu").setAttribute("style","");
        setPageElement("storyMenu", "StoryMenu", "");
    }
};

/*
**
** Wikifier object
**
*/

function Wikifier(place, source) {
    this.source = source;
    this.output = place;
    this.nextMatch = 0;
    this.assembleFormatterMatches(Wikifier.formatters);
    this.subWikify(this.output);
}

Wikifier.textPrimitives = {
    upperLetter: "[A-Z\u00c0-\u00de\u0150\u0170]",
    lowerLetter: "[a-z\u00df-\u00ff_0-9\\-\u0151\u0171]",
    anyLetter: "[A-Za-z\u00c0-\u00de\u00df-\u00ff_0-9\\-\u0150\u0170\u0151\u0171]"
}
Wikifier.textPrimitives.variable = "\\$((?:"+Wikifier.textPrimitives.anyLetter.replace("\\-", "")+"*"+
    Wikifier.textPrimitives.anyLetter.replace("0-9\\-", "")+"+"+
    Wikifier.textPrimitives.anyLetter.replace("\\-", "")+"*)+)";
Wikifier.textPrimitives.unquoted = "(?=(?:[^\"'\\\\]*(?:\\\\.|'(?:[^'\\\\]*\\\\.)*[^'\\\\]*'|\"(?:[^\"\\\\]*\\\\.)*[^\"\\\\]*\"))*[^'\"]*$)";

Wikifier.prototype.assembleFormatterMatches = function (formatters) {
    this.formatters = [];
    var pattern = [];

    for (var n = 0; n < formatters.length; n++) {
        pattern.push("(" + formatters[n].match + ")");
        this.formatters.push(formatters[n]);
    };

    this.formatterRegExp = new RegExp(pattern.join("|"), "mg");
};

Wikifier.prototype.subWikify = function (output, terminator) {
    // Temporarily replace the output pointer
    var terminatorMatch, formatterMatch, oldOutput = this.output;
    this.output = output;

    // Prepare the terminator RegExp
    var terminatorRegExp = terminator ? new RegExp("(" + terminator + ")", "mg") : null;
    do {
        // Prepare the RegExp match positions
        this.formatterRegExp.lastIndex = this.nextMatch;

        if (terminatorRegExp) terminatorRegExp.lastIndex = this.nextMatch;

        // Get the first matches
        formatterMatch = this.formatterRegExp.exec(this.source);
        terminatorMatch = terminatorRegExp ? terminatorRegExp.exec(this.source) : null;

        // Check for a terminator match
        if (terminatorMatch && (!formatterMatch || terminatorMatch.index <= formatterMatch.index)) {
            // Output any text before the match
            if (terminatorMatch.index > this.nextMatch) this.outputText(this.output, this.nextMatch, terminatorMatch.index);

            // Set the match parameters
            this.matchStart = terminatorMatch.index;
            this.matchLength = terminatorMatch[1].length;
            this.matchText = terminatorMatch[1];
            this.nextMatch = terminatorMatch.index + terminatorMatch[1].length;

            // Restore the output pointer and exit
            this.output = oldOutput;
            return;
        }
        // Check for a formatter match
        else if (formatterMatch) {
            // Output any text before the match
            if (formatterMatch.index > this.nextMatch) this.outputText(this.output, this.nextMatch, formatterMatch.index);

            // Set the match parameters
            this.matchStart = formatterMatch.index;
            this.matchLength = formatterMatch[0].length;
            this.matchText = formatterMatch[0];
            this.nextMatch = this.formatterRegExp.lastIndex;

            // Figure out which formatter matched
            var matchingFormatter = -1;
            for (var t = 1; t < formatterMatch.length; t++) {
                if (formatterMatch[t]) {
                    matchingFormatter = t - 1;
                    break;
                }
            }

            // Call the formatter
            if (matchingFormatter != -1) { this.formatters[matchingFormatter].handler(this); }
        }
    }
    while (terminatorMatch || formatterMatch);

    // Output any text after the last match
    if (this.nextMatch < this.source.length) {
        this.outputText(this.output, this.nextMatch, this.source.length);
        this.nextMatch = this.source.length;
    }

    // Restore the output pointer
    this.output = oldOutput;
};

Wikifier.prototype.outputText = function (place, startPos, endPos) {
    if (place) {
        insertText(place, this.source.substring(startPos, endPos));
    }
};

Wikifier.prototype.fullMatch = function() {
    return this.source.slice(this.matchStart, this.source.indexOf('>>', this.matchStart)+2);
};

Wikifier.prototype.fullArgs = function (includeName) {
    var source = this.source.replace(/\u200c/g," "),
        endPos = this.nextMatch-2,
        startPos = source.indexOf(includeName ? '<<' : ' ', this.matchStart);
    if (!~startPos || !~endPos || endPos <= startPos) {
        return "";
    }
    return Wikifier.parse(source.slice(startPos + (includeName ? 2 : 1), endPos).trim());
};

Wikifier.parse = function (input) {
    var m, re, b = input, found = [],
        g = Wikifier.textPrimitives.unquoted;
    
    function alter(from,to) {
        b = b.replace(new RegExp(from+g,"gim"),to);
        return alter;
    }
    // Extract all the variables, and set them to 0 if undefined.
    re = new RegExp(Wikifier.textPrimitives.variable+g,"gi");
    while (m = re.exec(input)) {
        if (!~found.indexOf(m[0])) {
            // This deliberately contains a 'null or undefined' check
            b = m[0]+" == null && ("+m[0]+" = 0);"+b;
            found.push(m[0]);
        }
    }
    alter(Wikifier.textPrimitives.variable, "state.history[0].variables.$1")
    // Old operators
    ("\\beq\\b", " == ")
    ("\\bneq\\b", " != ")
    ("\\bgt\\b", " > ")
    ("\\bgte\\b", " >= ")
    ("\\blt\\b", " < ")
    ("\\blte\\b", " <= ")
    ("\\band\\b", " && ")
    ("\\bor\\b", " || ")
    ("\\bnot\\b", " ! ")
    // New operators
    ("\\bis\\b", " == ")
    ("\\bto\\b", " = ");
    return b
};
Wikifier.formatHelpers = {
    charFormatHelper: function (a) {
        var b = insertElement(a.output, this.element);
        a.subWikify(b, this.terminator)
    },
    inlineCssHelper: function (w) {
        var s, v, lookaheadMatch, gotMatch,
            styles = [],
            lookahead = Wikifier.styleByCharFormatter.lookahead,
            lookaheadRegExp = new RegExp(lookahead, "mg"),
            hadStyle = false,
            unDash = function (str) {
                var s = str.split("-");
                if (s.length > 1) for (var t = 1; t < s.length; t++)
                s[t] = s[t].substr(0, 1).toUpperCase() + s[t].substr(1);
                return s.join("");
            };
        
        styles.className = "";
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            lookaheadMatch = lookaheadRegExp.exec(w.source);
            gotMatch = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (gotMatch) {
                hadStyle = true;
                if (lookaheadMatch[5]) {
                    styles.className += lookaheadMatch[5].replace(/\./g," ") + " ";
                } else if (lookaheadMatch[1]) {
                    s = unDash(lookaheadMatch[1]);
                    v = lookaheadMatch[2];
                } else {
                    s = unDash(lookaheadMatch[3]);
                    v = lookaheadMatch[4];
                }
                switch (s) {
                case "bgcolor":
                    s = "backgroundColor";
                    break;
                case "float":
                    s = "cssFloat";
                    break
                }
                styles.push({
                    style: s,
                    value: v
                });
                w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
            }
        } while (gotMatch);
        return styles;
    },
    monospacedByLineHelper: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source);
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) {
            insertElement(w.output, "pre", null, null, lookaheadMatch[1]);
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
};
Wikifier.formatters = [
{
    name: "table",
    match: "^\\|(?:[^\\n]*)\\|(?:[fhc]?)$",
    lookahead: "^\\|([^\\n]*)\\|([fhc]?)$",
    rowTerminator: "\\|(?:[fhc]?)$\\n?",
    cellPattern: "(?:\\|([^\\n\\|]*)\\|)|(\\|[fhc]?$\\n?)",
    cellTerminator: "(?:\\x20*)\\|",
    rowTypes: {
        "c": "caption",
        "h": "thead",
        "": "tbody",
        "f": "tfoot"
    },
    handler: function (w) {
        var rowContainer, rowElement,lookaheadMatch, matched,
            table = insertElement(w.output, "table"),
            lookaheadRegExp = new RegExp(this.lookahead, "mg"),
            currRowType = null,
            nextRowType,
            prevColumns = [],
            rowCount = 0;
        w.nextMatch = w.matchStart;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            lookaheadMatch = lookaheadRegExp.exec(w.source),
            matched = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (matched) {
                nextRowType = lookaheadMatch[2];
                if (nextRowType != currRowType) rowContainer = insertElement(table, this.rowTypes[nextRowType]);
                currRowType = nextRowType;
                if (currRowType == "c") {
                    if (rowCount == 0) rowContainer.setAttribute("align", "top");
                    else rowContainer.setAttribute("align", "bottom");
                    w.nextMatch = w.nextMatch + 1;
                    w.subWikify(rowContainer, this.rowTerminator);
                } else {
                    rowElement = insertElement(rowContainer, "tr");
                    this.rowHandler(w, rowElement, prevColumns);
                }
                rowCount++;
            }
        } while (matched);
    },
    rowHandler: function (w, e, prevColumns) {
        var cellMatch, matched, col = 0,
        currColCount = 1,
        cellRegExp = new RegExp(this.cellPattern, "mg");
        
        do {
            cellRegExp.lastIndex = w.nextMatch;
            cellMatch = cellRegExp.exec(w.source);
            matched = cellMatch && cellMatch.index == w.nextMatch;
            if (matched) {
                if (cellMatch[1] == "~") {
                    var last = prevColumns[col];
                    if (last) {
                        last.rowCount++;
                        last.element.setAttribute("rowSpan", last.rowCount);
                        last.element.setAttribute("rowspan", last.rowCount);
                        last.element.valign = "center";
                    }
                    w.nextMatch = cellMatch.index + cellMatch[0].length - 1;
                } else if (cellMatch[1] == ">") {
                    currColCount++;
                    w.nextMatch = cellMatch.index + cellMatch[0].length - 1;
                } else if (cellMatch[2]) {
                    w.nextMatch = cellMatch.index + cellMatch[0].length;
                    break;
                } else {
                    var spaceLeft = false,
                        spaceRight = false,
                        lastColCount, lastColElement, styles, cell, t;
                    w.nextMatch++;
                    styles = Wikifier.formatHelpers.inlineCssHelper(w);
                    while (w.source.substr(w.nextMatch, 1) == " ") {
                        spaceLeft = true;
                        w.nextMatch++;
                    }
                    if (w.source.substr(w.nextMatch, 1) == "!") {
                        cell = insertElement(e, "th");
                        w.nextMatch++;
                    } else cell = insertElement(e, "td");
                    prevColumns[col] = {
                        rowCount: 1,
                        element: cell
                    };
                    lastColCount = 1;
                    lastColElement = cell;
                    if (currColCount > 1) {
                        cell.setAttribute("colSpan", currColCount);
                        cell.setAttribute("colspan", currColCount);
                        currColCount = 1;
                    }
                    for (t = 0; t < styles.length; t++)
                    cell.style[styles[t].style] = styles[t].value;
                    w.subWikify(cell, this.cellTerminator);
                    if (w.matchText.substr(w.matchText.length - 2, 1) == " ") spaceRight = true;
                    if (spaceLeft && spaceRight) cell.align = "center";
                    else if (spaceLeft) cell.align = "right";
                    else if (spaceRight) cell.align = "left";
                    w.nextMatch = w.nextMatch - 1;
                }
                col++;
            }
        } while (matched);
    }
},
{
    name: "rule",
    match: "^----$\\n?",
    handler: function (w) {
        insertElement(w.output, "hr");
    }
},
{
    name: "emdash",
    match: "--",
    becomes: String.fromCharCode(8212),
    handler: function (a) {
        insertElement(a.output, "span", null, "char", this.becomes).setAttribute("data-char","emdash");
    }
},
{
    name: "heading",
    match: "^!{1,5}",
    terminator: "\\n",
    handler: function (w) {
        var e = insertElement(w.output, "h" + w.matchLength);
        w.subWikify(e, this.terminator);
    }
},
{
    name: "monospacedByLine",
    match: "^\\{\\{\\{\\n",
    lookahead: "^\\{\\{\\{\\n((?:^[^\\n]*\\n)+?)(^\\}\\}\\}$\\n?)",
    handler: Wikifier.formatHelpers.monospacedByLineHelper
},
{
    name: "quoteByBlock",
    match: "^<<<\\n",
    terminator: "^<<<\\n",
    handler: function (w) {
        var e = insertElement(w.output, "blockquote");
        w.subWikify(e, this.terminator);
    }
},
{
    name: "list",
    match: "^(?:(?:\\*+)|(?:#+))",
    lookahead: "^(?:(\\*+)|(#+))",
    terminator: "\\n",
    handler: function (w) {
        var newType, newLevel, t, len, bulletType, lookaheadMatch, matched,
            lookaheadRegExp = new RegExp(this.lookahead, "mg"),
            placeStack = [w.output],
            currType = null,
            currLevel = 0;
            
        w.nextMatch = w.matchStart;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            lookaheadMatch = lookaheadRegExp.exec(w.source);
            matched = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (matched) {
                newLevel = lookaheadMatch[0].length;
                if (lookaheadMatch[1]) {
                    bulletType = lookaheadMatch[1].slice(-1);
                    newType = "ul";
                }
                else if (lookaheadMatch[2]) {
                    newType = "ol";
                }
                w.nextMatch += newLevel;
                if (newLevel > currLevel) {
                    for (t = currLevel; t < newLevel; t++) {
                        placeStack.push(insertElement(placeStack[placeStack.length - 1], newType));
                    }
                } else if (newLevel < currLevel) {
                    for (t = currLevel; t > newLevel; t--)
                        placeStack.pop();
                } else if (newLevel == currLevel && newType != currType) {
                    placeStack.pop();
                    placeStack.push(insertElement(placeStack[placeStack.length - 1], newType));
                }
                currLevel = newLevel;
                currType = newType;
                t = insertElement(placeStack[placeStack.length - 1], "li");
                // Currently unused
                if (bulletType && bulletType != "*") {
                    t.setAttribute("data-bullet", bulletType);
                }
                w.subWikify(t, this.terminator);
            }
        } while (matched);
    }
},
(Wikifier.urlFormatter = {
    name: "urlLink",
    match: "(?:https?|mailto|javascript|ftp|data):[^\\s'\"]+(?:/|\\b)",
    handler: function (w) {
        var e = Wikifier.createExternalLink(w.output, w.matchText);
        w.outputText(e, w.matchStart, w.nextMatch);
    }
}),
(Wikifier.linkFormatter = {
    name: "prettyLink",
    match: "\\[\\[",
    lookahead: "\\[\\[([^\\|]*?)(?:\\|(.*?))?\\](?:\\[(.*?)\])?\\]",
    makeInternalOrExternal: function(out,title,callback,type) {
        if (title && !tale.has(title) && (title.match(Wikifier.urlFormatter.match,"g") || ~title.search(/[\.\\\/#]/)))
            return Wikifier.createExternalLink(out, title, callback, type); 
        else
            return Wikifier.createInternalLink(out, title, callback, type);
    },
    // This base callback executes the code in a setter 
    makeCallback: function(code,callback) {
        return function() {
            macros.set.run(null, Wikifier.parse(code), null, code); 
            typeof callback == "function" && callback.call(this);
        }
    },
    makeLink: function(out, match, callback2, type) {
        var link, title, callback;
        if (match[3]) { // Code
            callback = this.makeCallback(match[3],callback2);
        }
        else {
            typeof callback2 == "function" && (callback = callback2);
        }
        title = Wikifier.parsePassageTitle(match[2] || match[1]);
        link = this.makeInternalOrExternal(out,title,callback, type);
        setPageElement(link, null, match[2] ? match[1] : title);
        return link;
    },
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) {
            this.makeLink(w.output, lookaheadMatch)
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
}),
(Wikifier.imageFormatter = {
    name: "image",
    match: "\\[(?:[<]{0,1})(?:[>]{0,1})[Ii][Mm][Gg]\\[",
    lookahead: "\\[([<]?)(>?)img\\[(?:([^\\|\\]]+)\\|)?([^\\[\\]\\|]+)\\](?:\\[([^\\]]*)\\]?)?(\\])",
    importedImage: function(img, passageName) {
        var imgPassages, imgname;
        // Try to parse it as a variable
        try {
            imgname = internalEval(Wikifier.parse(passageName));
        }
        catch(e) {
        }
        if (!imgname) {
            imgname = passageName;
        }
        // Base64 passage transclusion
        imgPassages = tale.lookup("tags", "Twine.image");
        for (j = 0; j < imgPassages.length; j++) {
            if (imgPassages[j].title == imgname) {
                img.src = imgPassages[j].text;
                break;
            }
        }
    },
    handler: function (w) {
        var e, img, j, lookaheadMatch,
            lookaheadRegExp = new RegExp(this.lookahead, "mig");
        lookaheadRegExp.lastIndex = w.matchStart;
        lookaheadMatch = lookaheadRegExp.exec(w.source);
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart)
        {
            e = w.output, title = Wikifier.parsePassageTitle(lookaheadMatch[5])
            if (title) {
                e = Wikifier.linkFormatter.makeInternalOrExternal(w.output, title);
            }
            img = insertElement(e, "img");
            if (lookaheadMatch[1]) img.align = "left";
            else if (lookaheadMatch[2]) img.align = "right";
            if (lookaheadMatch[3]) img.title = lookaheadMatch[3];
            // Setup the image if it's referencing an image passage.
            this.importedImage(img,lookaheadMatch[4]);
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
}),
{
    name: "macro",
    match: "<<",
    lookahead: /<<([^>\s]+)(?:\s*)((?:\\.|'(?:[^'\\]*\\.)*[^'\\]*'|"(?:[^"\\]*\\.)*[^"\\]*"|[^'"\\>]|>(?!>))*)>>/mg,
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead);
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source.replace(/\u200c/g,'\n'));
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart && lookaheadMatch[1]) {
            var params = lookaheadMatch[2].readMacroParams();
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
            var name = lookaheadMatch[1];
            try {
                var macro = macros[name];
                if (macro && typeof macro == "object" && macro.handler) {
                    macro.handler(w.output, name, params, w);
                }
                // Variable?
                else if (name[0] == '$') {
                    macros.print.handler(w.output, name, [name].concat(params), w);
                }
                // Passage
                else if (tale.has(name)) {
                    macros.display.handler(w.output, name, [name].concat(params), w);
                }
                else throwError(w.output, 'No macro or passage called "' + name + '"', w.fullMatch());
            } catch (e) {
                throwError(w.output, 'Error executing macro ' + name + ': ' + e.toString(), w.fullMatch());
            }
        }
    }
},
{
    name: "html",
    match: "<html>",
    lookahead: "<html>((?:.|\\n)*?)</html>",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) {
            var e = insertElement(w.output, "span");
            e.innerHTML = lookaheadMatch[1];
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
},
{
    name: "commentByBlock",
    match: "/%",
    lookahead: "/%((?:.|\\n)*?)%/",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
    }
},
{
    name: "boldByChar",
    match: "''",
    terminator: "''",
    element: "strong",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "strikeByChar",
    match: "==",
    terminator: "==",
    element: "strike",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "underlineByChar",
    match: "__",
    terminator: "__",
    element: "u",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "italicByChar",
    match: "//",
    terminator: "//",
    element: "em",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "subscriptByChar",
    match: "~~",
    terminator: "~~",
    element: "sub",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "superscriptByChar",
    match: "\\^\\^",
    terminator: "\\^\\^",
    element: "sup",
    handler: Wikifier.formatHelpers.charFormatHelper
},
{
    name: "monospacedByChar",
    match: "\\{\\{\\{",
    lookahead: "\\{\\{\\{((?:.|\\n)*?)\\}\\}\\}",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) {
            var e = insertElement(w.output, "code", null, null, lookaheadMatch[1]);
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
},
(Wikifier.styleByCharFormatter = {
    name: "styleByChar",
    match: "@@",
    terminator: "@@",
    lookahead: "(?:([^\\(@]+)\\(([^\\)\\|\\n]+)(?:\\):))|(?:([^\\.:@]+):([^;\\|\\n]+);)|(?:\\.([^;\\|\\n]+);)",
    handler: function (w) {
        var e = insertElement(w.output, "span", null, null, null);
        var styles = Wikifier.formatHelpers.inlineCssHelper(w);
        if (styles.length == 0) {
            e.className = "marked";
        }
        else {
            for (var t = 0; t < styles.length; t++) {
                e.style[styles[t].style] = styles[t].value;
            }
            if (typeof styles.className == "string") {
                e.className = styles.className; 
            }
        }
        w.subWikify(e, this.terminator);
    }
}),
{
    name: "lineBreak",
    match: "\\n",
    handler: function (w) {
        insertElement(w.output, "br");
    }
},
{
    name: "continuedLine",
    match: "\\\\\\s*?\\n",
    handler: function(a) {
        a.nextMatch = a.matchStart+2;
    }
},
{
    name: "htmlCharacterReference",
    match: "(?:(?:&#?[a-zA-Z0-9]{2,8};|.)(?:&#?(?:x0*(?:3[0-6][0-9a-fA-F]|1D[c-fC-F][0-9a-fA-F]|20[d-fD-F][0-9a-fA-F]|FE2[0-9a-fA-F])|0*(?:76[89]|7[7-9][0-9]|8[0-7][0-9]|761[6-9]|76[2-7][0-9]|84[0-3][0-9]|844[0-7]|6505[6-9]|6506[0-9]|6507[0-1]));)+|&#?[a-zA-Z0-9]{2,8};)",
    handler: function(w)
    {
        var el = document.createElement("div");
        el.innerHTML = w.matchText;
        insertText(w.output, el.textContent);
    }
},
{
    name: "htmltag",
    match: "<(?:\\/?[\\w\\-]+|[\\w\\-]+(?:(?:\\s+[\\w\\-]+(?:\\s*=\\s*(?:\\\".*?\\\"|'.*?'|[^'\\\">\\s]+))?)+\\s*|\\s*)\\/?)>",
    tagname: "<(\\w+)",
    voids: ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"],
    tableElems: ["table","thead","tbody","tfoot","th","tr","td","colgroup","col","caption","figcaption"],
    cleanupTables: function (e) {
        var i, name, elems = [].slice.call(e.children);
        // Remove non-table child elements that aren't children of <td>s
        for (i = 0; i < elems.length; i++) {
            if (elems[i].tagName) {
                name = elems[i].tagName.toLowerCase();
                if (this.tableElems.indexOf(name)==-1) {
                    elems[i].outerHTML = '';
                }
                else if (['col','caption','figcaption','td','th'].indexOf(name)==-1) {
                    this.cleanupTables.call(this,elems[i]);
                }
            }
        }
    },
    handler: function (a) {
        var tmp, passage, setter, e, isvoid, isstyle, lookaheadRegExp, lookaheadMatch, lookahead,
          re = new RegExp(this.tagname).exec(a.matchText),
          tn = re && re[1] && re[1].toLowerCase();
        if(tn && tn != "html") {
            lookahead = "<\\/\\s*" + tn + "\\s*>";
            isvoid = (this.voids.indexOf(tn) != -1);
            isstyle = tn == "style" || tn == "script";
            lookaheadRegExp = new RegExp(lookahead, "mg");
            lookaheadRegExp.lastIndex = a.matchStart;
            lookaheadMatch = lookaheadRegExp.exec(a.source);
            if (lookaheadMatch || isvoid) {
                if (isstyle) {
                    e = document.createElement(tn);
                    e.type = "text/css"; // IE8 compatibility
                    tmp = a.source.slice(a.nextMatch, lookaheadMatch.index);
                    e.styleSheet ? (e.styleSheet.cssText = tmp) : (e.innerHTML = tmp);
                    a.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
                }
                else {
                    // Creating a loose <tr> element creates it wrapped inside a <tbody> element.
                    e = document.createElement(a.output.tagName);
                    e.innerHTML = a.matchText;
                    while(e.firstChild) {
                        e = e.firstChild;
                    }
                    if (!isvoid) {
                        a.subWikify(e, lookahead);
                    }
                }
                if (e.tagName.toLowerCase() == 'table') {
                    this.cleanupTables.call(this,e);
                }
                // Special data-setter attribute
                if (setter = e.getAttribute("data-setter")) {
                    setter = Wikifier.linkFormatter.makeCallback(setter);
                }
                // Special data-passage attribute
                if (passage = e.getAttribute("data-passage")) {
                    if (tn != "img") { 
                        addClickHandler(e, Wikifier.linkFunction(Wikifier.parsePassageTitle(passage), e, setter));
                        if (tn == "area" || tn == "a") {
                            e.setAttribute("href", "javascript:;");
                        }
                    }
                    else {
                        Wikifier.imageFormatter.importedImage(e, passage);
                    }
                }
                a.output.appendChild(e);
            } else {
                throwError(a.output,"HTML tag '"+tn+"' wasn't closed.", a.matchText);
            }
        }
    }
}];
// Optional - included if the ".char" selector appears anywhere in the story.
Wikifier.charSpanFormatter = {
    name: "char",
    match: "[^\n]",
    handler: function (a) {
        // Line breaks do NOT get their own charspans
        insertElement(a.output, "span", null, "char", a.matchText).setAttribute("data-char", a.matchText == " " ? "space" :
            a.matchText == "\t" ? "tab" : a.matchText);
    }
};

Wikifier.parsePassageTitle = function(title) {
    if (title && !tale.has(title)) {
        try {
            title = (internalEval(this.parse(title)) || title)+"";
        }
        catch(e) {}
    }
    return title;
};

Wikifier.linkFunction = function(title, el, callback) {
    return function() {
        if (state.rewindTo) {
            var passage = findPassageParent(el);
            if (passage && passage.parentNode.lastChild != passage) {
                state.rewindTo(passage, true);
            }
        }
        if (title) {
            state.display(title, el, null, callback);
        }
        else if (typeof callback == "function") {
            callback();
        }
    };
};

Wikifier.createInternalLink = function (place, title, callback, type) {
    var tag = (type == "button" ? 'button' : 'a'),
        suffix = (type == "button" ? "Button" : "Link"),
        el = insertElement(place, tag);

    if (tale.has(title)) {
        el.className = 'internal'+suffix;
        if (visited(title)) el.className += ' visited'+suffix;
    }
    else el.className = 'broken'+suffix;

    addClickHandler(el, Wikifier.linkFunction(title, el, callback));

    if (place) place.appendChild(el);

    return el;
};

Wikifier.createExternalLink = function (place, url, callback, type) {
    var tag = (type == "button" ? 'button' : 'a'),
        el = insertElement(place, tag);
    el.href = url;
    el.className = "external"+(type == "button" ? "Button" : "Link");
    el.target = "_blank";
    if (typeof callback == "function") {
        addClickHandler(el,callback);
    }
    
    if (place) place.appendChild(el);

    return el;
};

// Functions usable solely by custom scripts
// This includes restart(), above.
function visited(e) {
    var ret = 0, i = 0;
    if (!state) {
        return 0;
    }
    e = e || state.history[0].passage.title;
    if (arguments.length > 1) {
        for (ret = state.history.length; i<arguments.length; i++) {
            ret = Math.min(ret, visited(arguments[i]));
        }
    }
    else for(; i<state.history.length && state.history[i].passage; i++) {
        if(e == state.history[i].passage.title) {
            ret++;
        }
    }
    return ret;
}

// Returns the number of times the player visited passages containing ALL
// provided tags.
// The tags can be several strings, or a single string with space-delimited tags.
function visitedTag() {
    var i, j, sh, ret = 0, tags = Array.prototype.slice.call(arguments);
    if (tags.length == 1 && typeof tags[0] == "string") {
        tags = tags.split(" ");
    }
    if (!state) {
        return 0;
    }
    sh = state.history;
    for(i = 0; i<sh.length && sh[i].passage; i++) {
        for (j = 0; j < tags.length || void ret++; j++) {
            if(sh[i].passage.tags.indexOf(tags[j])==-1) {
                break;
            }
        }
    }
    return ret;
}
var visitedTags = visitedTag;

function turns() {
    return state.history.length-1;
}

function passage() {
    return state.history[0].passage.title
}

function tags(e) {
    var ret = [], i = 0;
    if (!state) {
        return 0;
    }
    e = e || state.history[0].passage.title;
    if (arguments.length > 1) {
        for (i = arguments.length-1; i >= 1; i--) {
            ret = ret.concat(tags(arguments[i]));
        }
    }
    ret = ret.concat(tale.get(e).tags);
    return ret;
}

function previous() {
    if (state && state.history[1]) {
        for (var d = 1; d < state.history.length && state.history[d].passage; d++) {
            if (state.history[d].passage.title != state.history[0].passage.title) {
                return state.history[d].passage.title
            }
        }
    }
    return ""
}

// A random integer function
// 1 argument: random int from 0 to a inclusive
// 2 arguments: random int from a to b inclusive (order irrelevant)
function random(a, b) {
    var from, to;
    if (!b) {
        from = 0;
        to = a;
    } else {
        from = Math.min(a, b);
        to = Math.max(a, b);
    }
    to += 1;
    return ~~((Math.random() * (to - from))) + from;
}

function either() {
    if (Array.isArray(arguments[0]) && arguments.length == 1) {
        return either.apply(this,arguments[0]);
    }
    return arguments[~~(Math.random()*arguments.length)];
}

function parameter(n) {
    n = n || 0;
    if (macros.display.parameters[n]) {
        return macros.display.parameters[n];
    }
    return 0
}

function bookmark() {
    return state.hash || "#";
}

/* Used to eval within Twine, but outside the context of a particular function */
function internalEval(s) {
    // eval("{x:1,y:1}") fails miserably unless the obj. literal
    // is not the first expression in the line (hence, "0,").
    return eval("0,"+s);
}
/* Used to execute script passages */
function scriptEval(s) {
    try {
        eval(s.text);
    } catch (e) {
        alert("There is a technical problem with this " + tale.identity() + " (" + s.title + ": " + e.message + ")."+softErrorMessage);
    }
}
/* Unload prompt */
window.onbeforeunload = function() {
    if (tale && tale.storysettings.lookup("exitprompt",false) && state && state.history.length > 1) {
        return "You are about to end this " + tale.identity() + ".";
    }
};
/* Error reporting */
var oldOnError = window.onerror || null, 
softErrorMessage = "You may be able to continue playing, but some parts may not work properly.";

window.onerror = function (msg, a, b, c, error) {
    var s = (error && (".\n\n" + error.stack.replace(/\([^\)]+\)/g,'') + "\n\n")) || (" (" + msg + ").\n");
    alert("Sorry to interrupt, but this " + ((tale && tale.identity && tale.identity()) || "page") + "'s code has got itself in a mess" + s + softErrorMessage.slice(1));
    // Restore previous onerror
    window.onerror = oldOnError;
    if (typeof window.onerror == "function") {
        window.onerror(msg, a, b, c, error);
    }
};

/* Init function */
var $;
function main() {
    // Used by old custom scripts.
    // Cedes to jQuery if it exists.
    // Since jQuery is inserted after this script element,
    // wait until main() is called before doing this.
    $ = window.$ || function(a) {
        return (typeof a == "string" ? document.getElementById(a) : a);
    }
    var imgs, scripts, macro, style, i,
        styleText = "",
        passages = document.getElementById("passages");
    
    // Run checks after custom macros are installed
    function sanityCheck(thing) {
        var i, j, s = "NOTE: The " + thing,
            checks = { prerender: prerender, postrender: postrender, macros: macros };
        // Warn if prerender/postrender/macros aren't objects, and
        // prerender/postrender's own properties aren't functions.
        for (i in checks) {
            if (Object.prototype.hasOwnProperty.call(checks, i) && !sanityCheck[i]) {
                if (!checks[i] || typeof checks[i]  != "object") {
                    alert(s + " seems to have corrupted the " + i + " object."+softErrorMessage);
                    sanityCheck[i] = true;
                    continue;
                }
                if (i != "macros") {
                    for (j in checks[i]) {
                        if (Object.prototype.hasOwnProperty.call(checks[i], j)
                                && typeof checks[i][j] != "function") {
                            alert(s + " added a property '" + j + "' to " + i + ", "
                                +"which is a "+typeof checks[i][j]+", not a function."+softErrorMessage);
                            sanityCheck[i] = true;
                            break;
                        }
                    }
                }
            }
        }
    }
    
    // Check for basic compatibility
    if (!window.JSON || !document.querySelector) {
        return (passages.innerHTML = "This " + tale.identity() + " requires a newer web browser. Sorry.");
    } else {
        passages.innerHTML = "";
    }
    // Initialise Tale
    tale = window.tale = new Tale();
    
    // Check for IE8 image compatibility
    if (~document.documentElement.className.indexOf("lt-ie9")) {
        imgs = tale.lookup("tags", "Twine.image");
        for (i = 0; i < imgs.length; i++) {
            if (imgs[i].text.length >= 32768) {
                alert("NOTE: This " + tale.identity() + "'s HTML file contains embedded images that may be too large for this browser to display."+softErrorMessage);
                break;
            }
        }
    }
    // Run all script passages
    scripts = tale.lookup("tags", "script");
    for (i = 0; i < scripts.length; i++) {
        scriptEval(scripts[i]);
        sanityCheck('script passage "'+scripts[i].title+'"');
    }
    // Need to create state now, since it's used by remember.init()
    state = window.state = new History();
    for (i in macros) {
        macro = macros[i];
        if (typeof macro.init == "function") {
            macro.init();
            sanityCheck('init() of the custom macro "'+i+'"');
        }
    }
    // Run all stylesheet passages
    style = document.getElementById("storyCSS");
    for (i in tale.passages) {
        i = tale.passages[i];
        if (i.tags.indexOf("stylesheet")==-1) {
            continue;
        }
        // No other tags?
        if (i.tags + "" == "stylesheet") {
            styleText += i.text;
        }
        else if (i.tags.length == 2 && i.tags.indexOf("transition") >-1) {
            setTransitionCSS(i.text);
        }
    }
    styleText = alterCSS(styleText);
    style.styleSheet ? (style.styleSheet.cssText = styleText) : (style.innerHTML = styleText);
    
    state.init();
}

setTimeout(function f() {
    var size, bar = document.getElementById("loadingbar"), store = document.getElementById("storeArea");
    if (!bar) {
        return;
    }
    if (store) {
        size = store.getAttribute("data-size");
        if (store.children.length <= size && !tale) {
            // +1 so that the bar can reach the end
            bar.style.width = ~~((store.children.length+1)/size*100)+"%";
        }
        else {
            bar.outerHTML = "";
            return;
        }
    }
    setTimeout(f,5);
},5);
