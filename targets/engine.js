function clone(a) {
    var b = {};
    for (var property in a) {
        b[property] = a[property]
    }
    return b
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
    if (place = document.getElementById(c)) {
        removeChildren(place);
        if (tale.has(b)) {
            new Wikifier(place, tale.get(b).text)
        } else {
            new Wikifier(place, a)
        }
    }
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

function throwError(a, b) {
    new Wikifier(a, "'' @@ " + b + " @@ ''")
}
Math.easeInOut = function (a) {
    return (1 - ((Math.cos(a * Math.PI) + 1) / 2))
};
String.prototype.readMacroParams = function () {
    var c = new RegExp("(?:\\s*)(?:(?:\"([^\"]*)\")|(?:'([^']*)')|(?:\\[\\[([^\\]]*)\\]\\])|([^\"'\\s]\\S*))", "mg");
    var b = [];
    do {
        var a = c.exec(this);
        if (a) {
            if (a[1]) {
                b.push(a[1]);
            } else if (a[2]) {
                b.push(a[2]);
            } else if (a[3]) {
                b.push(a[3]);
            } else if (a[4]) {
                b.push(a[4]);
            }
        }
    } while (a);
    return b
};
String.prototype.readBracketedList = function () {
    var b = "\\[\\[([^\\]]+)\\]\\]";
    var a = "[^\\s$]+";
    var e = "(?:" + b + ")|(" + a + ")";
    var d = new RegExp(e, "mg");
    var f = [];
    do {
        var c = d.exec(this);
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
                c.onComplete()
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

function scrollWindowTo(e) {
    var d = window.scrollY ? window.scrollY : document.body.scrollTop;
    var g = k(e);
    var c = Math.abs(d - g);
    var b = 0;
    var j = (d > g) ? -1 : 1;
    var f = window.setInterval(h, 25);

    function h() {
        b += 0.1;
        window.scrollTo(0, d + j * (c * Math.easeInOut(b)));
        if (b >= 1) {
            window.clearInterval(f)
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

function History() {
    this.history = [{
        passage: null,
        variables: {},
        hash: null
    }]
}
History.prototype.restart = function () {
    window.location.reload();
};
History.prototype.save = function (c) {
    var a = "";
    for (var b = this.history.length - 1; b >= 0; b--) {
        if ((this.history[b].passage) && (this.history[b].passage.id)) {
            a += this.history[b].passage.id.toString(36) + "."
        }
    }
    return "#" + a.substr(0, a.length - 1)
};
History.prototype.restore = function () {
    try {
        if ((window.location.hash == "") || (window.location.hash == "#")) {
            return false
        }
        if (window.location.hash.substr(0, 2) == '#!') {
            var mt = window.location.hash.substr(2).split('_').join(' ');
            document.getElementById('passages').appendChild(this.display(mt, null, 'quietly'));
            return true;
        }
        var a = window.location.hash.replace("#", "").split(".");
        for (var b = 0; b < a.length; b++) {
            var g = parseInt(a[b], 36);
            if (!tale.has(g)) {
                return false
            }
            if (b == a.length - 1) {
              this.display(g, null, f);
            }
            else
              tale.get(g).render();
        }
        return true
    } catch (d) {
        return false
    }
};
History.prototype.watchHash = function () {
    if (window.location.hash != this.hash) {
        if ((window.location.hash != "") && (window.location.hash != "#")) {
            this.history = [{
                passage: null,
                variables: {}
            }];
            removeChildren(document.getElementById("passages"));
            if (!this.restore()) {
                alert("The passage you had previously visited could not be found.")
            }
        } else {
            window.location.reload()
        }
        this.hash = window.location.hash
    }
};
var version = {
    major: 2,
    minor: 1,
    revision: 0,
    date: new Date("January 1, 2013"),
    extensions: {}
};
var tale, state, macros = window.macros = {};

window.onpopstate = function(e) {
    if (e.state && e.state.length > 0) {
        state.history = e.state;
    } else {
        state = new History();
        state.init();
    }
    state.display(state.history[0].passage.title,null,"back");
}
macros.refresh = {
    handler: function (a, b, c) {
        window.location.reload()
    }
};
version.extensions.displayMacro = {
    major: 1,
    minor: 0,
    revision: 0
};
macros.display = {
    handler: function (a, b, c) {
        if (c[0] == "_previous") {
            if (state.history[1]) {
                for (var d = 1; d <= state.history.length; d++) {
                    if (state.history[d].passage.title != state.history[0].passage.title) {
                        break
                    }
                }
                var e = state.history[d].passage.title;
                new Wikifier(a, tale.get(e).text)
            } else {
                return
            }
        } else {
            if (tale.get(c[0]).id == undefined) {
                throwError(a, "The " + c[0] + " passage does not exist");
                return
            } else {
                new Wikifier(a, tale.get(c[0]).text)
            }
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
        var e = insertElement(a, "ul");
        if (!state.history[0].variables["actions clicked"]) {
            state.history[0].variables["actions clicked"] = {}
        }
        for (var b = 0; b < g.length; b++) {
            if (state.history[0].variables["actions clicked"][g[b]]) {
                continue
            }
            var d = insertElement(e, "li");
            var c = Wikifier.createInternalLink(d, g[b]);
            insertText(c, g[b]);
            c.onclick = function () {
                state.history[0].variables["actions clicked"][this.id] = true;
                state.display(this.id, c)
            }
        }
    }
};
version.extensions.printMacro = {
    major: 1,
    minor: 1,
    revision: 1
};
macros['print'] = {
    handler: function (place, macroName, params, parser) {
        try {
            var output = eval(parser.fullArgs());
            if (output != null && (typeof output !== "number" || !isNaN(output))) {
                new Wikifier(place, output.toString());
            }
        } catch (e) {
            throwError(place, "printMacro bad expression: " + e.message);
        }
    }
};
version.extensions.setMacro = {
    major: 1,
    minor: 1,
    revision: 0
};
macros.set = {
    handler: function (a, b, c, d) {
        macros.set.run(a,d.fullArgs())
    },
    run: function (a,expression) {
        try {
            return eval(Wikifier.parse(expression))
        } catch (e) {
            throwError(a, "bad expression: " + e.message)
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
                    conditions.push(currentCond);
                    clauses.push(currentClause);
                    break;
                }
            }
            if ((src.substr(i, 6) == "<<else") && nesting == 0) {
                conditions.push(currentCond);
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
                    if (eval(conditions.shift())) {
                        new Wikifier(place, clauses[i].trim());
                        break;
                    }
                }
            } else {
                throwError(place, "can't find matching endif");
            }
        } catch (e) {
            throwError(place, "bad condition: " + e.message);
        }
    }
};
macros["else"] = macros["endif"] = {
    handler: function () {}
};

version.extensions.rememberMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros['remember'] = {
    handler: function (place, macroName, params, parser) {
        var statement = parser.fullArgs();
        var variable, value;
        macros.set.run(place,statement);
        variable = statement.match(Wikifier.textPrimitives.variable)[1];
        value = eval(Wikifier.parse("$" + variable));
        switch (typeof value) {
        case "string":
            value = '"' + value.replace(/"/g, '\\"') + '"';
            break;
        case "number":
        case "boolean":
            break;
        default:
            throwError(place, "can't remember $" + variable + " (" + (typeof value) + ")");
            return;
        }
        if (this.uselocalstorage) {
            localStorage[this.prefix + variable] = value;
        } else {
            document.cookie = this.prefix + variable + "=" + value + "; expires=" + this.expire;
        }
    },
    init: function () {
        var expiredate = new Date();
        expiredate.setYear(expiredate.getFullYear() + 1);
        this.expire = expiredate.toGMTString();
        if (tale.has("StoryTitle")) {
            this.prefix = tale.get("StoryTitle").text + "_";
        } else {
            this.prefix = "__twineremember_";
        }
        if (typeof localStorage != 'undefined' && localStorage !== null) {
            this.uselocalstorage = true;
            for (var i in localStorage) {
                if (i.indexOf(this.prefix) == 0) {
                    var variable = i.substr(this.prefix.length);
                    var value = localStorage[i];
                    eval(Wikifier.parse('$' + variable + ' = ' + value));
                }
            }
        } else {
            this.uselocalstorage = false;
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var bits = cookies[i].split("=");
                if (bits[0].trim().indexOf(this.prefix) == 0) {
                    var statement = cookies[i].replace(this.prefix, "$");
                    eval(Wikifier.parse(statement));
                }
            }
        }
    },
    expire: null,
    uselocalstorage: null,
    prefix: null,
};

version.extensions.SilentlyMacro = {
    major: 1,
    minor: 0,
    revision: 0
};
macros.silently = {
    handler: function (g, e, f, b) {
        var h = insertElement(null, 'div');
        var k = b.source.indexOf('>>', b.matchStart) + 2;
        var a = b.source.slice(k);
        var d = -1;
        var c = '';
        var l = 0;
        for (var i = 0; i < a.length; i++) {
            if (a.substr(i, 15) == '<<endsilently>>') {
                if (l == 0) {
                    d = k + i + 15;
                    break;
                } else {
                    l--;
                }
            } else if (a.substr(i, 12) == '<<silently>>') {
                l++;
            }
            c += a.charAt(i);
        };
        if (d != -1) {
            new Wikifier(h, c);
            b.nextMatch = d;
        } else {
            throwError(g, "can't find matching endsilently");
        }
    }
};
macros.endsilently = {
    handler: function () {}
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
    if (a && a != "") {
        return a.replace(/\\n/mg, "\n").replace(/\\s/mg, "\\").replace(/\\/mg, "\\").replace(/\r/mg, "")
    } else {
        return ""
    }
};
function Tale() {
    this.passages = {};
    var a,b,c,lines,i,kv,ns,nsc,nope,
        settings = this.storysettings = {},
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
    };
    //Look for and load the StorySettings
    if (document.normalize) document.normalize();
    a = document.getElementById("storeArea").childNodes;
    for (b = 0; b < a.length; b++) {
        c = a[b];
        if (c.getAttribute && c.getAttribute("tiddler") == 'StorySettings') {
            lines = new Passage('StorySettings', c, 0, null, null).text.split('\n');
            for (i in lines) {
                if (lines[i].indexOf(':') > -1) {
                    kv = lines[i].split(':');
                    kv[0] = kv[0].replace(/^\s+|\s+$/g, '');
                    kv[1] = kv[1].replace(/^\s+|\s+$/g, '');
                    settings[kv[0]] = kv[1];
                }
            }
        }
    }
    //Load in the passages
    if (settings['obfuscate'] == 'swap' && settings['obfuscatekey']) {
        ns = '';
        nope = ":\\\"n0";
        if (settings['obfuscatekey'] == 'rot13') {
            settings['obfuscatekey'] = "anbocpdqerfsgthuivjwkxlymz";
        }
        for (i = 0; i < settings['obfuscatekey'].length; i++) {
            nsc = settings['obfuscatekey'][i];
            if (ns.indexOf(nsc) == -1 && nope.indexOf(nsc) == -1) ns = ns + nsc;
        }
        settings['obfuscatekey'] = ns;
        for (b = 0; b < a.length; b++) {
            c = a[b];
            if (c.getAttribute && (tiddlerTitle = c.getAttribute("tiddler"))) {
                if (tiddlerTitle != 'StorySettings') 
                    tiddlerTitle = deswap(tiddlerTitle, settings['obfuscatekey']);
                this.passages[tiddlerTitle] = new Passage(tiddlerTitle, c, b, deswap, settings['obfuscatekey']);
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
        for (i in this.passages) {
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
        for (i in this.passages) {
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
        var e = false;
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
function Wikifier(place, source) {
    this.source = source;
    this.output = place;
    this.nextMatch = 0;
    this.assembleFormatterMatches(Wikifier.formatters);
    this.subWikify(this.output);
};

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
    var oldOutput = this.output;
    this.output = output;

    // Prepare the terminator RegExp
    var terminatorRegExp = terminator ? new RegExp("(" + terminator + ")", "mg") : null;
    do {
        // Prepare the RegExp match positions
        this.formatterRegExp.lastIndex = this.nextMatch;

        if (terminatorRegExp) terminatorRegExp.lastIndex = this.nextMatch;

        // Get the first matches
        var formatterMatch = this.formatterRegExp.exec(this.source);
        var terminatorMatch = terminatorRegExp ? terminatorRegExp.exec(this.source) : null;

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
            for (var t = 1; t < formatterMatch.length; t++)
            if (formatterMatch[t]) matchingFormatter = t - 1;

            // Call the formatter
            if (matchingFormatter != -1) { this.formatters[matchingFormatter].handler(this); }
        }
    }
    while (terminatorMatch || formatterMatch);

    // Output any text after the last match
    if (this.nextMatch < this.source.length) {
        this.outputText(this.output, this.nextMatch, this.source.length);
        this.nextMatch = this.source.length;
    };

    // Restore the output pointer
    this.output = oldOutput;
};

Wikifier.prototype.outputText = function (place, startPos, endPos) {
    insertText(place, this.source.substring(startPos, endPos));
};

Wikifier.prototype.fullArgs = function () {
    var startPos = this.source.indexOf(' ', this.matchStart);
    var endPos = this.source.indexOf('>>', this.matchStart);

    return Wikifier.parse(this.source.slice(startPos, endPos).trim());
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
        var styles = [];
        var lookahead = "(?:(" + Wikifier.textPrimitives.anyLetter + "+)\\(([^\\)\\|\\n]+)(?:\\):))|(?:(" + Wikifier.textPrimitives.anyLetter + "+):([^;\\|\\n]+);)";
        var lookaheadRegExp = new RegExp(lookahead, "mg");
        var hadStyle = false;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            var lookaheadMatch = lookaheadRegExp.exec(w.source);
            var gotMatch = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
            if (gotMatch) {
                var s, v;
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
                    j = "cssFloat";
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
        var table = insertElement(w.output, "table");
        w.nextMatch = w.matchStart;
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        var currRowType = null,
            nextRowType;
        var rowContainer, rowElement;
        var prevColumns = [];
        var rowCount = 0;
        do {
            lookaheadRegExp.lastIndex = w.nextMatch;
            var lookaheadMatch = lookaheadRegExp.exec(w.source),
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
        var col = 0;
        var currColCount = 1;
        var cellRegExp = new RegExp(this.cellPattern, "mg");
        do {
            cellRegExp.lastIndex = w.nextMatch;
            var cellMatch = cellRegExp.exec(w.source),
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
                    w.nextMatch = cellMatch.index + cellMatch[0].length;;
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
    handler: function (w) {
        var e = insertElement(w.output, "span");
        e.innerHTML = '&mdash;';
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
{
    name: "prettyLink",
    match: "\\[\\[",
    lookahead: "\\[\\[([^\\|\\]]*?)(?:(\\]\\])|(\\|(.*?)\\]\\]))",
    terminator: "\\|",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source)
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart && lookaheadMatch[2]) // Simple bracketted link
        {
            var link = Wikifier.createInternalLink(w.output, lookaheadMatch[1]);
            w.outputText(link, w.nextMatch, w.nextMatch + lookaheadMatch[1].length);
            w.nextMatch += lookaheadMatch[1].length + 2;
        } else if (lookaheadMatch && lookaheadMatch.index == w.matchStart && lookaheadMatch[3]) // Pretty bracketted link
        {
            var e;
            if (tale.has(lookaheadMatch[4])) e = Wikifier.createInternalLink(w.output, lookaheadMatch[4]);
            else e = Wikifier.createExternalLink(w.output, lookaheadMatch[4]);
            w.outputText(e, w.nextMatch, w.nextMatch + lookaheadMatch[1].length);
            w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
        }
    }
},
{
    name: "urlLink",
    match: "(?:http|https|mailto|ftp):[^\\s'\"]+(?:/|\\b)",
    handler: function (w) {
        var e = Wikifier.createExternalLink(w.output, w.matchText);
        w.outputText(e, w.matchStart, w.nextMatch);
    }
},
{
    name: "image",
    match: "\\[(?:[<]{0,1})(?:[>]{0,1})[Ii][Mm][Gg]\\[",
    lookahead: "\\[([<]?)(>?)img\\[(?:([^\\|\\]]+)\\|)?([^\\[\\]\\|]+)\\](?:\\[([^\\]]*)\\]?)?(\\])",
    handler: function (w) {
        var lookaheadRegExp = new RegExp(this.lookahead, "mg");
        lookaheadRegExp.lastIndex = w.matchStart;
        var lookaheadMatch = lookaheadRegExp.exec(w.source);
        if (lookaheadMatch && lookaheadMatch.index == w.matchStart) // Simple bracketted link
        {
            var e = w.output;
            if (lookaheadMatch[5]) {
                if (tale.has(lookaheadMatch[5])) e = Wikifier.createInternalLink(w.output, lookaheadMatch[5]);
                else e = Wikifier.createExternalLink(w.output, lookaheadMatch[5]);
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
},
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
            try {
                var macro = macros[lookaheadMatch[1]];
                if (macro && macro.handler) macro.handler(w.output, lookaheadMatch[1], params, w);
                else throwError(w.output, 'Macro not found: ' + lookaheadMatch[1]);
            } catch (e) {
                throwError(w.output, 'Error executing macro ' + lookaheadMatch[1] + ': ' + e.toString());
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
        if (styles.length == 0) e.className = "marked";
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
    match: "\\\\\\n",
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
          doit = false,
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
                throwError(a.output,"HTML tag '"+tn+"' wasn't closed.");
            }
        }
    }
}
];
Wikifier.createInternalLink = function (place, title) {
    var el = insertElement(place, 'a', title);
    el.href = 'javascript:void(0)';

    if (tale.has(title)) el.className = 'internalLink';
    else el.className = 'brokenLink';

    el.onclick = function () {
        state.display(title, el)
    };

    if (place) place.appendChild(el);

    return el;
};
Wikifier.createExternalLink = function (place, url) {
    var el = insertElement(place, 'a');
    el.href = url;
    el.className = 'externalLink';
    el.target = '_blank';

    if (place) place.appendChild(el);

    return el;
};
Wikifier.textPrimitives = {};
if (!((new RegExp("[\u0150\u0170]", "g")).test("\u0150"))) {
    Wikifier.textPrimitives.upperLetter = "[A-Z\u00c0-\u00de]";
    Wikifier.textPrimitives.lowerLetter = "[a-z\u00df-\u00ff_0-9\\-]";
    Wikifier.textPrimitives.anyLetter = "[A-Za-z\u00c0-\u00de\u00df-\u00ff_0-9\\-]"
} else {
    Wikifier.textPrimitives.upperLetter = "[A-Z\u00c0-\u00de\u0150\u0170]";
    Wikifier.textPrimitives.lowerLetter = "[a-z\u00df-\u00ff_0-9\\-\u0151\u0171]";
    Wikifier.textPrimitives.anyLetter = "[A-Za-z\u00c0-\u00de\u00df-\u00ff_0-9\\-\u0150\u0170\u0151\u0171]"
};
Wikifier.textPrimitives.variable = "\\$((?:"+Wikifier.textPrimitives.anyLetter.replace("\\-", "\\.")+"|\\[[^\\]]+\\])+)";
    
/* Functions usable by custom scripts */
function visited(e) {
    var ret,c;
    e || (e = state.history[0].passage.title);
    for(ret=c=0; c<state.history.length; c++) {
        if(state.history[c].passage && state.history[c].passage.title == e) {
            ret++;
        }
    }
    return ret;
}
/* Init function */
function main() {
    // Used by old custom scripts.
    // Cedes to jQuery if it exists.
    var $ = window.$ || function(a) {
        return (typeof a == "string" ? document.getElementById(a) : a);
    }
    tale = window.tale = new Tale();
    state = window.state = new History();
    document.title = tale.title;
    setPageElement("storyTitle", "StoryTitle", "Untitled Story");
    setPageElement("storySubtitle", "StorySubtitle", "");
    if (tale.has("StoryAuthor")) {
        document.getElementById("titleSeparator").innerHTML = "<br>";
        setPageElement("storyAuthor", "StoryAuthor", "");
    }
    if (tale.has("StoryMenu")) {
        document.getElementById("storyMenu").style.display = "inline";
        setPageElement("storyMenu", "StoryMenu", "");
    }
    var scripts = tale.lookup("tags", "script");
    for (var i = 0; i < scripts.length; i++) {
        try {
            eval(scripts[i].text);
        } catch (e) {
            alert("There is a technical problem with this story (" + scripts[i].title + ": " + e.message + "). You may be able to continue reading, but all parts of the story may not work properly.");
        }
    }
    for (var macroidx in macros) {
        var macro = macros[macroidx];
        if (typeof macro.init == "function") {
            macro.init();
        }
    }
    var styles = tale.lookup("tags", "stylesheet");
    for (var i = 0; i < styles.length; i++) {
        addStyle(styles[i].text);
    }
    state.init();
};
