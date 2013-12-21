function clone(a) {
    var b = {};
    for (var property in a) {
        if (typeof a[property] == "object") {
            try {
                b[property] = JSON.parse(JSON.stringify(a[property]));
                continue;
            }
            catch(e) {}
        }
        b[property] = a[property];
    }
    return b;
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

function insertText(a, b) {
    return a.appendChild(document.createTextNode(b))
}

function removeChildren(a) {
    while (a.hasChildNodes()) {
        a.removeChild(a.firstChild)
    }
}

function setPageElement(c, b, a) {
    var place;
    if (place = (typeof c == "string" ? document.getElementById(c) : c)) {
        removeChildren(place);
        if (tale.has(b)) {
            new Wikifier(place, tale.get(b).text)
        } else {
            new Wikifier(place, a)
        }
    }
}
// Kept for custom script use
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
    var imgPassages = tale.lookup("tags", "Twine.image");
    // Remove comments
    text = text.replace(/\/\*(?:[^\*]|\*(?!\/))*\*\//g,'');
    // Add images
    return text.replace(new RegExp(Wikifier.imageFormatter.lookahead, "gim"), function(m,p1,p2,p3,src) {
        for (var i = 0; i < imgPassages.length; i++) {
            if (imgPassages[i].title == src) {
                src = imgPassages[i].text;
                break;
            }
        }
        return "url(" + src + ");"
    });
}

function setTransitionCSS(styleText) {
    styleText = alterCSS(styleText);
    var style = document.getElementById("transitionCSS");
    style.styleSheet ? (style.styleSheet.cssText = styleText) : (style.innerHTML = styleText);
}

function throwError(a, b, tooltip) {
    var elem = insertElement(a, "span", null, "marked", b);
    tooltip && elem.setAttribute("title", tooltip);
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
String.prototype.trim || (String.prototype.trim = function () {
    return this.replace(/^\s\s*/, "").replace(/\s\s*$/, "")
});
String.prototype.unDash = function () {
    var s = this.split("-");
    if (s.length > 1) for (var t = 1; t < s.length; t++)
    s[t] = s[t].substr(0, 1).toUpperCase() + s[t].substr(1);
    return s.join("");
}
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
/* btoa/atob polyfill by github.com/davidchambers */
(function(){function t(t){this.message=t}var e=window,r="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";t.prototype=Error(),t.prototype.name="InvalidCharacterError",e.btoa||(e.btoa=function(e){for(var o,n,a=0,i=r,c="";e.charAt(0|a)||(i="=",a%1);c+=i.charAt(63&o>>8-8*(a%1))){if(n=e.charCodeAt(a+=.75),n>255)throw new t();o=o<<8|n}return c}),e.atob||(e.atob=function(e){if(e=e.replace(/=+$/,""),1==e.length%4)throw new t();for(var o,n,a=0,i=0,c="";n=e.charAt(i++);~n&&(o=a%4?64*o+n:n,a++%4)?c+=String.fromCharCode(255&o>>(6&-2*a)):0)n=r.indexOf(n);return c})})();

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

var scrollWindowInterval;
function scrollWindowTo(e) {
    var d = window.scrollY ? window.scrollY : document.body.scrollTop;
    var g = k(e);
    var c = Math.abs(d - g);
    var b = 0;
    var j = (d > g) ? -1 : 1;
    scrollWindowInterval = window.setInterval(h, 25);

    function h() {
        b += 0.1;
        window.scrollTo(0, d + j * (c * Math.easeInOut(b)));
        if (b >= 1) {
            window.clearInterval(scrollWindowInterval)
        }
    }

    function k(o) {
        var p = a(o);
        var q = p + o.offsetHeight;
        var l = window.scrollY ? window.scrollY : document.body.scrollTop;
        var m = window.innerHeight ? window.innerHeight : document.body.clientHeight;
        var n = l + m;
        if (p < l) {
            return p
        } else {
            if (q > n) {
                if (o.offsetHeight < m) {
                    return (p - (m - o.offsetHeight) + 20)
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

function History() {
    this.history = [{
        passage: null,
        variables: {},
        hash: null
    }]
}

History.prototype.encodeHistory = function(b, noVars) {
    var ret = ".", vars, type, hist = this.history[b],
        d = this.history[b+1] ? delta(this.history[b+1].variables, hist.variables) : hist.variables;
    
    function vtob(str) {
        try {
            return window.btoa(unescape(encodeURIComponent(JSON.stringify(str))));
        } catch(e) {
            return "0";
        }
    }
    
    if (!hist.passage || hist.passage.id == undefined) {
        return ""
    }
    ret += hist.passage.id.toString(36)
    if (noVars) {
        return ret;
    }
    for (vars in d) {
        type = typeof d[vars];
        if (type != "function" && type != "undefined") {
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
}

History.prototype.decodeHistory = function(str, prev) {
    var name, splits, variable, c, d, 
        ret = { variables: prev.variables || {} },
        match = /([a-z0-9]+)((?:\$[A-Za-z0-9\+\/=]+,[A-Za-z0-9\+\/=]+)*)((?:\[[A-Za-z0-9\+\/=]+,[A-Za-z0-9\+\/=]+)*)/g.exec(str);
    
    function btov(str) {
        try {
            return JSON.parse(decodeURIComponent(escape(window.atob(str))));
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
}

History.prototype.save = function (c) {
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
        if (testplay) {
            this.display(testplay, null, 'quietly');
            return true
        }
        if (!window.location.hash || (window.location.hash == "#")) {
            return false
        }
        if (window.location.hash.substr(0, 2) == '#!') {
            c = window.location.hash.substr(2).split('_').join(' ');
            this.display(c, null, 'quietly');
            return true
        }
        a = window.location.hash.replace("#", "").split(".");
        for (b = 0; b < a.length; b++) {
            vars = this.decodeHistory(a[b], vars || {});
            if (vars) {
                if (b == a.length - 1) {
                    vars.variables = this.history[0].variables;
                    for (c in this.history[0].linkVars) {
                        vars.variables[c] = this.history[0].linkVars[c];
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
var version = {
    major: 4,
    minor: 0,
    revision: 0,
    date: new Date("November 28, 2013"),
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
            params = name.readMacroParams(true);
            try {
                for(j=0; j < params.length; j++) {
                    params[j] = eval(Wikifier.parse(params[j]));
                }
            } catch (e) {
                throwError(place, "<<" + macroName + " " + name + ">> bad argument: " + params[j], parser.fullMatch());
                return
            }
        }
        else {
            try {
                output = eval(name);
            }
            catch(e) {
                // Last-ditch attempt
                if (tale.get(name).id) {
                    output = name;
                }
                else {
                    throwError(place, "<<" + macroName + ">> bad expression: " + e.message,
                        parser.fullMatch());
                    return
                }
            }
        }
        t = tale.get(output+"");
        if (!output) {
            throwError(place, '"' +name + "\" did not evaluate to a passage name", parser.fullMatch());
        } else if (t.id === undefined) {
            throwError(place, "The \"" + output + "\" passage does not exist", parser.fullMatch());
        } else {
            oldDisplayParams = this.parameters;
            this.parameters = params;
            if (t.tags.indexOf("script") > -1) {
                scriptEval(t);
            }
            else {
                new Wikifier(place, tale.get(output+"").processText());
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
        try {
            var args = parser.fullArgs(macroName != "print"),
                output = eval(args);
            if (output != null && (typeof output != "number" || !isNaN(output))) {
                new Wikifier(place, output.toString());
            }
        } catch (e) {
            throwError(place, "<<print>> bad expression: " + e.message, parser.fullMatch());
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
        macros.set.run(a, parser.fullArgs(), parser)
    },
    run: function (a,expression, parser) {
        try {
            return eval(Wikifier.parse(expression));
        } catch (e) {
            throwError(a, "bad expression: " + e.message, parser ? parser.fullMatch() : expression)
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
            srcOffset = parser.source.indexOf(">>", parser.matchStart) + 2,
            src = parser.source.slice(srcOffset),
            endPos = -1,
            currentCond = parser.fullArgs(),
            currentClause = "",
            t = 0,
            nesting = 0;
        for (var i = 0; i < src.length; i++) {
            if (src.substr(i, 9) == "<<endif>>") {
                nesting--;
                if (nesting < 0) {
                    endPos = srcOffset + i + 9;
                    conditions.push(currentCond.trim());
                    clauses.push(currentClause);
                    break;
                }
            }
            if ((src.substr(i, 6) == "<<else") && !nesting) {
                conditions.push(currentCond.trim());
                clauses.push(currentClause);
                currentClause="";
                t = src.indexOf(">>",i+6);
                if(src.substr(i+6,4)==" if " || src.substr(i+6,3)=="if ") {
                    currentCond = Wikifier.parse(src.slice(i+9,t));
                }
                else {
                    currentCond = "true";
                }
                i = t+2;
            }
            if (src.substr(i, 5) == "<<if ") {
                nesting++;
            }
            currentClause += src.charAt(i);
        }
        try {
            if (endPos != -1) {
                parser.nextMatch = endPos;
                for(i=0;i<clauses.length;i++) {
                    if (eval(conditions[i])) {
                        new Wikifier(place, clauses[i]);
                        break;
                    }
                }
            } else {
                throwError(place, "can't find matching endif", parser.fullMatch());
            }
        } catch (e) {
            throwError(place, "<<if>> bad condition: " + e.message, !i ? parser.fullMatch()
                : "<<else if " + conditions[i] + ">>");
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
        macros.set.run(place, parser.fullArgs());
        if (!window.localStorage) {
            throwError(place, "<<remember>> can't be used "
                + (window.location.protocol == "file:" ? " by local HTML files " : "") + " in this browser.");
            return;
        }
        re = new RegExp(Wikifier.textPrimitives.variable, "g");
        while (match = re.exec(statement)) {
            variable = match[1];
            value = state.history[0].variables[variable];
            try {
                value = JSON.stringify(value);
            } catch (e) {
                throwError(place, "can't remember $" + variable + " (" + (typeof value) + ")", parser.fullMatch());
                return;
            }
            window.localStorage[this.prefix + variable] = value;
        }
    },
    init: function () {
        var i, variable, value;
        if (tale.has("StoryTitle")) {
            this.prefix = "Twine." + tale.get("StoryTitle").text + ".";
        } else {
            this.prefix = "Twine.Untitled Story.";
        }
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
                    d = k + i + 15;
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
            throwError(place, "can't find matching end" + macroName, parser.fullMatch());
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
    handler: function (A, C, D, parser) {
        var link, id, match, temp, callback,
            text = D[1] || D[0].split("|")[0],
            clicked = function() { return state.history[0].variables["choice clicked"] || 
                    (state.history[0].variables["choice clicked"] = {})},
            passage = A;
        while(passage && !~passage.className.indexOf("passage")) {
            passage = passage.parentNode;
        }
        // Get ID of the "choice clicked" entry
        id = (passage && passage.id.replace(/\|[^\]]*$/,''));
        if (id && clicked()[id]) {
            insertElement(A, "span", null, "disabled", text); 
        }
        else {
            callback = function() {
                var i, other = passage.querySelectorAll(".choice");
                onclick && onclick();
                for (i = 0; i < other.length; i++) {
                    other[i].outerHTML = "<span class=disabled>" + other[i].innerHTML + "</span>";
                }
                clicked()[id] = true;
            };
            match = new RegExp(Wikifier.linkFormatter.lookahead).exec(parser.fullArgs());
            
            if (match) {
                link = Wikifier.linkFormatter.makeLink(match,A,callback);
            }
            else {
                link = Wikifier.createInternalLink(A, D[0], callback);
                setPageElement(link, null, text);
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
    handler: function (a, b, e) {
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
                    stepsParam2 = eval(Wikifier.parse(stepsParam2));
                }
                catch(r) {
                    throwError(a, b + "Macro bad expression: " + r.message)
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
        if(labelParam == -1) {
            labelParam = e.indexOf("labeldefault");
        }
        if(labelParam > -1) {
            if(!e[labelParam + 1]) {
                throwError(a, e[labelParam] + 'keyword needs an additional label parameter');
                return;
            }
            labeltouse = e[labelParam + 1];
            if(e[labelParam] == 'labeldefault') this.labeltext = labeltouse;
            e.splice(labelParam, 2);
        }
        // What's left is the passage name parameter
        if(stepsParam <= 0) {
            if(e[0]) {
                if(e[0].charAt(0) == '$') {
                    try {
                        e = eval(Wikifier.parse(e[0]));
                    }
                    catch(r) {
                        throwError(a, "<<" + b + ">> bad expression: " + r.message)
                        return;
                    }
                }
                else {
                    e = e[0];
                }
                if(tale.get(e).id == undefined) {
                    throwError(a, "The \"" + e + "\" passage does not exist");
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
        el.onclick = (function(b) { return function () {
            return macros.back.onclick(b == "back", steps)
        }}(b));
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

function Passage(c, b, a, ofunc, okey) {
    this.title = c;
    if (b) {
        this.id = a;
        if (ofunc != null && typeof ofunc == 'function' && okey != null) {
            var t = b.firstChild ? b.firstChild.nodeValue : "";
            t = ofunc(t, okey);
            this.initialText = this.text = Passage.unescapeLineBreaks(t);
            this.tags = b.getAttribute("tags");
            if (typeof this.tags == "string") {
                this.tags = ofunc(this.tags, okey);
                this.tags = this.tags.readBracketedList();
            } else this.tags = [];
        } else {
            this.initialText = this.text = Passage.unescapeLineBreaks(b.firstChild ? b.firstChild.nodeValue : "");
            this.tags = b.getAttribute("tags");
            if (typeof this.tags == "string") this.tags = this.tags.readBracketedList();
            else this.tags = [];
        }
    } else {
        this.initialText = this.text = '@@This passage does not exist: ' + c + '@@';
        this.tags = [];
    }
}
Passage.unescapeLineBreaks = function (a) {
    if (a && typeof a == "string") {
        return a.replace(/\\n/mg, "\n").replace(/\\s/mg, "\\").replace(/\\/mg, "\\").replace(/\r/mg, "")
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
        ret = ret.replace(/\n/g,'\u200c');
    }
    if (~this.tags.indexOf("Twine.image")) {
        ret = "[img[" + ret + "]]"
    }
    return ret;
};

function Tale() {
    this.passages = {};
    var a,b,c,lines,i,kv,ns,nsc,nope,
        settings = this.storysettings = {
            lookup: function(a) {
                return !~["0", "off", "false"].indexOf((this[a]+"").toLowerCase());
            }
        },
        tiddlerTitle = '';
    function deswap(t, k) {
        var i,c,p,p1,up,r = '';
        for (i = 0; i < t.length; i++) {
            c = t.charAt(i);
            up = (c == c.toUpperCase());
            p = k.indexOf(c.toLowerCase());
            if (p > -1) {
                p1 = p + (p % 2 == 0 ? 1 : -1);
                if (p1 >= k.length) p1 = p;
                c = k.charAt(p1);
                up && (c = c.toUpperCase());
            }
            r = r + c;
        }
        return r
    }
    //Look for and load the StorySettings
    if (document.normalize) document.normalize();
    a = document.getElementById("storeArea").children;
    for (b = 0; b < a.length; b++) {
        c = a[b];
        if (c.getAttribute && c.getAttribute("tiddler") == 'StorySettings') {
            lines = new Passage('StorySettings', c, 0, null, null).text.split('\n');
            for (i in lines) {
                if (typeof lines[i] == "string" && lines[i].indexOf(':') > -1) {
                    kv = lines[i].split(':');
                    kv[0] = kv[0].replace(/^\s+|\s+$/g, '');
                    kv[1] = kv[1].replace(/^\s+|\s+$/g, '');
                    settings[kv[0]] = kv[1];
                }
            }
        }
    }
    //Load in the passages
    if (settings.obfuscate == 'swap' && settings.obfuscatekey) {
        ns = '';
        nope = ":\\\"n0";
        if (settings.obfuscatekey == 'rot13') {
            settings.obfuscatekey = "anbocpdqerfsgthuivjwkxlymz";
        }
        for (i = 0; i < settings.obfuscatekey.length; i++) {
            nsc = settings.obfuscatekey[i];
            if (ns.indexOf(nsc) == -1 && nope.indexOf(nsc) == -1) ns = ns + nsc;
        }
        settings.obfuscatekey = ns;
        for (b = 0; b < a.length; b++) {
            c = a[b];
            if (c.getAttribute && (tiddlerTitle = c.getAttribute("tiddler"))) {
                if (tiddlerTitle != 'StorySettings') 
                    tiddlerTitle = deswap(tiddlerTitle, settings.obfuscatekey);
                this.passages[tiddlerTitle] = new Passage(tiddlerTitle, c, b+1, deswap, settings.obfuscatekey);
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
    this.title = (this.passages.StoryTitle ? this.passages.StoryTitle.text : document.title);
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
    return this.storysettings.lookup('undo');
};
Tale.prototype.forEachStylesheet = function(tags, callback) {
    var passage, i
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

function Wikifier(place, source) {
    this.source = source;
    this.output = place;
    this.nextMatch = 0;
    this.assembleFormatterMatches(Wikifier.formatters);
    this.subWikify(this.output);
}

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
    insertText(place, this.source.substring(startPos, endPos));
};

Wikifier.prototype.fullMatch = function() {
    return this.source.slice(this.matchStart, this.source.indexOf('>>', this.matchStart)+2);
};

Wikifier.prototype.fullArgs = function (includeName) {
    var endPos = this.source.indexOf('>>', this.matchStart),
        startPos = this.source.indexOf(includeName ? '<<' : ' ', this.matchStart);
    if (!~startPos || !~endPos || endPos <= startPos) {
        return "";
    }
    return Wikifier.parse(this.source.slice(startPos + (includeName ? 2 : 1), endPos).trim());
};

Wikifier.parse = function (input) {
    var m, re, b = input, found = [],
        g = "(?=(?:[^\"'\\\\]*(?:\\\\.|'(?:[^'\\\\]*\\\\.)*[^'\\\\]*'|\"(?:[^\"\\\\]*\\\\.)*[^\"\\\\]*\"))*[^'\"]*$)";
    
    function alter(from,to) {
        return b.replace(new RegExp(from+g,"gi"),to);
    }
    // Extract all the variables, and set them to 0 if undefined.
    re = new RegExp(Wikifier.textPrimitives.variable,"gi");
    while (m = re.exec(input)) {
        if (!~found.indexOf(m[0])) {
            // This deliberately contains a 'null or undefined' check
            b = m[0]+" == null && ("+m[0]+" = 0);"+b;
            found.push(m[0]);
        }
    }
    b = alter(Wikifier.textPrimitives.variable, "state.history[0].variables.$1");
    // Old operators
    b = alter("\\beq\\b", " == ");
    b = alter("\\bneq\\b", " != ");
    b = alter("\\bgt\\b", " > ");
    b = alter("\\bgte\\b", " >= ");
    b = alter("\\blt\\b", " < ");
    b = alter("\\blte\\b", " <= ");
    b = alter("\\band\\b", " && ");
    b = alter("\\bor\\b", " || ");
    b = alter("\\bnot\\b", " ! ");
    // New operators
    b = alter("\\bis\\b", " == ");
    b = alter("\\bto\\b", " = ");
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
            lookahead = "(?:(" + Wikifier.textPrimitives.anyLetter + "+)\\(([^\\)\\|\\n]+)(?:\\):))|(?:(" + Wikifier.textPrimitives.anyLetter + "+):([^;\\|\\n]+);)",
            lookaheadRegExp = new RegExp(lookahead, "mg"),
            hadStyle = false;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            lookaheadMatch = lookaheadRegExp.exec(w.source);
            gotMatch = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (gotMatch) {
                hadStyle = true;
                if (lookaheadMatch[1]) {
                    s = lookaheadMatch[1].unDash();
                    v = lookaheadMatch[2];
                } else {
                    s = lookaheadMatch[3].unDash();
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
            var text = lookaheadMatch[1];

            // IE specific hack
            if (navigator.userAgent.indexOf("msie") != -1 && navigator.userAgent.indexOf("opera") == -1) text = text.replace(/\n/g, "\r");
            var e = insertElement(w.output, "pre", null, null, text);
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
    handler: function (a) {
        insertElement(a.output, "span", null, "char " + (a.matchText == " " ? "space" : a.matchText), a.matchText);
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
    name: "monospacedByLineForPlugin",
    match: "^//\\{\\{\\{\\n",
    lookahead: "^//\\{\\{\\{\\n\\n*((?:^[^\\n]*\\n)+?)(\\n*^//\\}\\}\\}$\\n?)",
    handler: Wikifier.formatHelpers.monospacedByLineHelper
},
{
    name: "wikifyCommentForPlugin",
    match: "^/\\*\\*\\*\\n",
    terminator: "^\\*\\*\\*/\\n",
    handler: function (w) {
        w.subWikify(w.output, this.terminator);
    }
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
    name: "quoteByLine",
    match: "^>+",
    terminator: "\\n",
    element: "blockquote",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.match, "mg");
        var placeStack = [w.output];
        var currLevel = 0;
        var newLevel = w.matchLength;
        var t;
        do {
            if (newLevel > currLevel) {
                for (t = currLevel; t < newLevel; t++)
                placeStack.push(insertElement(placeStack[placeStack.length - 1], this.element));
            } else if (newLevel < currLevel) {
                for (t = currLevel; t > newLevel; t--)
                placeStack.pop();
            }
            currLevel = newLevel;
            w.subWikify(placeStack[placeStack.length - 1], this.terminator);
            lookaheadRegExp.lastIndex = w.nextMatch;
            var lookaheadMatch = lookaheadRegExp.exec(w.source);
            var matched = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (matched) {
                newLevel = lookaheadMatch[0].length;
                w.nextMatch += lookaheadMatch[0].length;
                insertElement(placeStack[placeStack.length - 1], "br");
            }
        } while (matched);
    }
},
{
    name: "list",
    match: "^(?:(?:\\*+)|(?:#+))",
    lookahead: "^(?:(\\*+)|(#+))",
    terminator: "\\n",
    outerElement: "ul",
    itemElement: "li",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        w.nextMatch = w.matchStart;
        var placeStack = [w.output];
        var currType = null,
            newType;
        var currLevel = 0,
            newLevel;
        var t;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            var lookaheadMatch = lookaheadRegExp.exec(w.source);
            var matched = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (matched) {
                if (lookaheadMatch[1]) newType = "ul";
                if (lookaheadMatch[2]) newType = "ol";
                newLevel = lookaheadMatch[0].length;
                w.nextMatch += lookaheadMatch[0].length;
                if (newLevel > currLevel) {
                    for (t = currLevel; t < newLevel; t++)
                    placeStack.push(insertElement(placeStack[placeStack.length - 1], newType));
                } else if (newLevel < currLevel) {
                    for (t = currLevel; t > newLevel; t--)
                    placeStack.pop();
                } else if (newLevel == currLevel && newType != currType) {
                    placeStack.pop();
                    placeStack.push(insertElement(placeStack[placeStack.length - 1], newType));
                }
                currLevel = newLevel;
                currType = newType;
                var e = insertElement(placeStack[placeStack.length - 1], "li");
                w.subWikify(e, this.terminator);
            }
        } while (matched);
    }
},
(Wikifier.urlFormatter = {
    name: "urlLink",
    match: "(?:http|https|mailto|javascript|ftp|data):[^\\s'\"]+(?:/|\\b)",
    handler: function (w) {
        var e = Wikifier.createExternalLink(w.output, w.matchText);
        w.outputText(e, w.matchStart, w.nextMatch);
    }
}),
(Wikifier.linkFormatter = {
    name: "prettyLink",
    match: "\\[\\[",
    lookahead: "\\[\\[([^\\|\\]]*?)(?:\\|(.*?))?\\](?:\\[(.*?)\])?\\]",
    makeInternalOrExternal: function(out,title,callback) {
        if (title && !tale.has(title) && (title.match(Wikifier.urlFormatter.match) || ~title.search(/[\.\\\/#]/)))
            return Wikifier.createExternalLink(out, title, callback); 
        else
            return Wikifier.createInternalLink(out, title, callback);
    },
    makeLink: function(match, out, callback2) {
        var link, title, callback;
        if (match[3]) { // Code
            callback = function() {
                macros.set.run(out, match[3]); 
                typeof callback2 == "function" && callback2();
            };
        }
        else {
            typeof callback2 == "function" && (callback = callback2);
        }
        title = Wikifier.parsePassageTitle(match[2] || match[1]);
        link = this.makeInternalOrExternal(out,title,callback);
        setPageElement(link, null, match[2] ? match[1] : title);
        return link;
    },
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) {
            this.makeLink(lookaheadMatch, w.output)
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
}),
(Wikifier.imageFormatter = {
    name: "image",
    match: "\\[(?:[<]{0,1})(?:[>]{0,1})[Ii][Mm][Gg]\\[",
    lookahead: "\\[([<]?)(>?)img\\[(?:([^\\|\\]]+)\\|)?([^\\[\\]\\|]+)\\](?:\\[([^\\]]*)\\]?)?(\\])",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mig");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source);
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) // Simple bracketed link
        {
            var e = w.output, title = Wikifier.parsePassageTitle(lookaheadMatch[5])
            if (title) {
                e = Wikifier.linkFormatter.makeInternalOrExternal(w.output, title);
            }
            var img = insertElement(e, "img");
            if (lookaheadMatch[1]) img.align = "left";
            else if (lookaheadMatch[2]) img.align = "right";
            if (lookaheadMatch[3]) img.title = lookaheadMatch[3];
            img.src = lookaheadMatch[4];
            // Base64 passage transclusion
            var imgPassages = tale.lookup("tags", "Twine.image");
            for (var j = 0; j < imgPassages.length; j++) {
                if (imgPassages[j].title == lookaheadMatch[4]) {
                    img.src = imgPassages[j].text;
                    break;
                }
            }
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
}),
{
    name: "macro",
    match: "<<",
    lookahead: "<<([^>\\s]+)(?:\\s*)((?:[^>]|>(?!>))*)>>",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart && lookaheadMatch[1]) {
            var params = lookaheadMatch[2].readMacroParams();
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
            var name = lookaheadMatch[1];
            try {
                var macro = macros[name];
                if (macro && macro.handler) {
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
                else throwError(w.output, 'Macro not found: ' + name, w.fullMatch());
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
{
    name: "styleByChar",
    match: "@@",
    terminator: "@@",
    lookahead: "(?:([^\\(@]+)\\(([^\\)]+)(?:\\):))|(?:([^:@]+):([^;]+);)",
    handler: function (w) {
        var e = insertElement(w.output, "span", null, null, null);
        var styles = Wikifier.formatHelpers.inlineCssHelper(w);
        if (styles.length == 0)
            e.className = "marked";
        else for (var t = 0; t < styles.length; t++)
            e.style[styles[t].style] = styles[t].value;
        w.subWikify(e, this.terminator);
    }
},
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
    name: "htmltag",
    match: "<\\w+(?:(?:\\s+\\w+(?:\\s*=\\s*(?:\".*?\"|'.*?'|[^'\">\\s]+))?)+\\s*|\\s*)\\/?>",
    tagname: "<(\\w+)",
    voids: ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"],
    handler: function (a) {
        var e, isvoid, lookaheadRegExp, lookaheadMatch, lookahead,
          re = new RegExp(this.tagname).exec(a.matchText),
          tn = re && re[1];
        if(tn && tn.toLowerCase() != "html") {
            lookahead = "<\\/\\s*" + tn + "\\s*>";
            isvoid = (this.voids.indexOf(tn.toLowerCase()) != -1);
            lookaheadRegExp = new RegExp(lookahead, "mg");
            lookaheadRegExp.lastIndex = a.matchStart;
            lookaheadMatch = lookaheadRegExp.exec(a.source);
            if (lookaheadMatch || isvoid) {
                e = document.createElement(a.output.tagName);
                e.innerHTML = a.matchText;
                e = e.firstChild;
                if (!isvoid) {
                    a.subWikify(e, lookahead);
                }
                a.output.appendChild(e);
            } else {
                throwError(a.output,"HTML tag '"+tn+"' wasn't closed.", a.matchText);
            }
        }
    }
},
{
    name: "char",
    match: ".",
    handler: function (a) {
        insertElement(a.output, "span", null, "char " + (a.matchText == " " ? "space" : a.matchText), a.matchText);
    }
}
];
Wikifier.parsePassageTitle = function(title) {
    if (title && !tale.has(title)) {
        try {
            title = eval(this.parse(title))
            title && (title += "");
        }
        catch(e) {}
    }
    return title;
}
Wikifier.createExternalLink = function (place, url) {
    var el = insertElement(place, 'a');
    el.href = url;
    el.className = 'externalLink';
    el.target = '_blank';

    if (place) place.appendChild(el);

    return el;
};
if (!((new RegExp("[\u0150\u0170]", "g")).test("\u0150"))) {
    Wikifier.textPrimitives = {
        upperLetter: "[A-Z\u00c0-\u00de]",
        lowerLetter: "[a-z\u00df-\u00ff_0-9\\-]",
        anyLetter: "[A-Za-z\u00c0-\u00de\u00df-\u00ff_0-9\\-]"
    }
} else {
    Wikifier.textPrimitives = {
        upperLetter: "[A-Z\u00c0-\u00de\u0150\u0170]",
        lowerLetter: "[a-z\u00df-\u00ff_0-9\\-\u0151\u0171]",
        anyLetter: "[A-Za-z\u00c0-\u00de\u00df-\u00ff_0-9\\-\u0150\u0170\u0151\u0171]"
    }
};
Wikifier.textPrimitives.variable = "\\$((?:"+Wikifier.textPrimitives.anyLetter.replace("\\-", "\\.")+"*"+
    Wikifier.textPrimitives.anyLetter.replace("0-9\\-", "\\.")+"+"+
    Wikifier.textPrimitives.anyLetter.replace("\\-", "\\.")+"*)+)";
    
/* Functions usable by custom scripts */
function visited(e) {
    var ret = 0, i = 0;
    e = e || state.history[0].passage.title;
    if (arguments.length > 1) {
        for (ret = state.history.length; i<arguments.length; i++) {
            ret = Math.min(ret, visited(arguments[i]));
        }
    } else for(; i<state.history.length && state.history[i].passage; i++) {
        if(~e.indexOf(state.history[i].passage.title)) {
            ret++;
        }
    }
    return ret;
}
function passage() {
    return state.history[0].passage.title
}
function tags(e) {
    var ret = [], i = 0;
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
    if (state.history[1]) {
        for (var d = 1; d < state.history.length && state.history[d].passage; d++) {
            if (state.history[d].passage.title != state.history[0].passage.title) {
                return state.history[d].passage.title
            }
        }
    }
    return ""
}
function either() {
    return arguments[~~(Math.random()*arguments.length)];
}
function parameter(n) {
    n = n || 0;
    if (macros.display.parameters[n]) {
        return macros.display.parameters[n];
    }
    return 0
}

function scriptEval(s) {
    try {
        eval(s.text);
    } catch (e) {
        alert("There is a technical problem with this story (" + s.title + ": " + e.message + "). You may be able to continue reading, but parts of the story may not work properly.");
    }
}
/* Init function */
var $;
function main() {
    // Used by old custom scripts.
    // Cedes to jQuery if it exists.
    $ = window.$ || function(a) {
        return (typeof a == "string" ? document.getElementById(a) : a);
    }
    var imgs, scripts, macro, style, styleText = "", i, passages = document.getElementById("passages");
    
    if (!window.JSON) {
        return (passages.innerHTML = "This story requires a newer web browser. Sorry.");
    } else {
        passages.innerHTML = "";
    }
    tale = window.tale = new Tale();
    document.title = tale.title;
    
    if (~document.documentElement.className.indexOf("lt-ie9")) {
        imgs = tale.lookup("tags", "Twine.image");
        for (i = 0; i < imgs.length; i++) {
            if (imgs[i].text.length >= 32768) {
                alert("NOTE: This story's HTML file contains embedded images that may be too large for this browser to display.");
                break;
            }
        }
    }
    
    setPageElement("storyTitle", "StoryTitle", "Untitled Story");
    setPageElement("storySubtitle", "StorySubtitle", "");
    if (tale.has("StoryAuthor")) {
        setPageElement("titleSeparator", null, "\n");
        setPageElement("storyAuthor", "StoryAuthor", "");
    }
    if (tale.has("StoryMenu")) {
        document.getElementById("storyMenu").style.display = "inline";
        setPageElement("storyMenu", "StoryMenu", "");
    }
    scripts = tale.lookup("tags", "script");
    for (i = 0; i < scripts.length; i++) {
        scriptEval(scripts[i]);
    }
    for (macro in macros) {
        macro = macros[macro];
        if (typeof macro.init == "function") {
            macro.init();
        }
    }
    style = document.getElementById("storyCSS");
    for (i in tale.passages) {
        i = tale.passages[i];
        if (i.tags + "" == "stylesheet") {
            styleText += alterCSS(i.text);
        }
        else if (i.tags.length == 2 && i.tags.indexOf("transition") >-1 &&
                i.tags.indexOf("stylesheet") >-1) {
            setTransitionCSS(i.text);
        }
    }
    style.styleSheet ? (style.styleSheet.cssText = styleText) : (style.innerHTML = styleText);
    
    state = window.state = new History();
    state.init();
}
