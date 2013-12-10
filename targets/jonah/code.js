/*
**
** Jonah specific code follows
**
*/
Tale.prototype.canBookmark = function() {
    return this.canUndo() && (this.storysettings.lookup('bookmark'));
};
History.prototype.init = function () {
    if (!this.restore()) {
        if (tale.has("StartPassages")) {
            var B = tale.get("StartPassages").text.readBracketedList();
            for (var A = 0; A < B.length; A++) {
                this.display(B[A], null, "quietly")
            }
        } else {
            this.display("Start", null, "quietly")
        }
    }
};
History.prototype.closeLinks = function() {
    var i, p, D, l = document.querySelectorAll("#passages .internalLink");
    for(i = l.length-1; i >= 0; i--) {
        D = insertElement(null, "span", null, "disabled");
        D.innerHTML = l[i].innerHTML;
        p = l[i].parentNode;
        p.insertBefore(D, l[i].nextSibling);
        p.removeChild(l[i]);
    }
    l = document.querySelectorAll(".toolbar");
    for(i = l.length-1; i >= 0; i--) {
        l[i].parentNode.removeChild(l[i]);
    }
};
History.prototype.display = function (name, source, type, callback) {
    var el, D, F, p = document.getElementById("passages");
    if (!tale.canUndo()) {
        this.closeLinks()
    }
    if (el = document.getElementById("passage" + name)) {
        el.id += "|" + (new Date).getTime();
    }
    D = tale.get(name);
    this.history.unshift({
        passage: D,
        variables: clone(this.history[0].variables)
    });
    if (typeof callback == "function") {
        callback();
        this.history[1] && (this.history[1].linkVars = delta(this.history[1].variables,this.history[0].variables));
    }
    F = D.render();
    if (type != "offscreen" && type != "quietly") {
        if (hasTransition) {
            F.classList.add("transition-in");
            setTimeout(function () {
                F.classList.remove("transition-in");
            }, 1);
            F.style.visibility = "visible"
        }
        p.appendChild(F);
        scrollWindowTo(F);
        if (!hasTransition) {
            fade(F, {
                fade: "in"
            });
        }
    }
    else {
        p.appendChild(F);
        F.style.visibility = "visible"
    }
    return F
};
History.prototype.rewindTo = function (C, instant) {
    var B = this;

    var p2, p = document.getElementById("passages").lastChild;
    while (p && p != C) {
        p2 = p.previousSibling;
        if (instant) {
            p.parentNode.removeChild(p);
        }
        else if (hasTransition) {
            p.classList.add("transition-out");
            setTimeout((function(p) { return function () {
                    if(p.parentNode) p.parentNode.removeChild(p);
                }}(p)), 1000);
        } else {
            fade(p, {
                fade: "out", 
                onComplete: function() { this.parentNode.removeChild(this); }
            });
        }
        B.history.shift();
        p = p2;
    }
};
Passage.prototype.render = function () {
    var F, D, A, t, i, E = insertElement(null, 'div', 'passage' + this.title, 'passage');
    E.style.visibility = 'hidden';
    this.setTags(E);
    this.setCSS();
    F = insertElement(E, 'div', '', 'title', this.title);
    D = insertElement(F, 'span', '', 'toolbar');
    for (i = 0; i < Passage.toolbarItems.length && tale.canUndo(); i++) {
        t = Passage.toolbarItems[i];
        if (t.label == "bookmark" && !tale.canBookmark()) {
            continue;
        }
        var C = insertElement(D, 'a', null, "toolbar-" + t.label);
        insertText(C, t.label);
        C.passage = this;
        if (t.href) {
            C.href = t.href(E)
        }
        C.title = t.tooltip;
        C.onclick = t.activate
        C.div = E;
    }
    A = insertElement(E, 'div', '', 'body content');
    for (i in prerender) {
        (typeof prerender[i] == "function") && prerender[i].call(this,A);
    }
    new Wikifier(A, this.processText());
    for (i in postrender) {
        (typeof postrender[i] == "function") && postrender[i].call(this,A);
    }
    return E
};
Passage.prototype.reset = function () {
    this.text = this.initialText
};
Passage.toolbarItems = [{
    label: "bookmark",
    tooltip: "Bookmark this point in the story",
    href: function (A) {
        return (state.save(A))
    },
    activate: function () {}
}, {
    label: "rewind to here",
    tooltip: "Rewind the story to this point",
    activate: function () {
        state.rewindTo(this.div)
    }
}];
Passage.transitionCache = "";
Passage.prototype.setCSS = function() {
    var trans = false, text = "", tags = this.tags || [],
        c = document.getElementById('transitionCSS');
    
    if (c && c.getAttribute('data-tags') != tags.join(' ')) {
        tale.forEachStylesheet(tags, function(passage) {
            if (~passage.tags.indexOf("transition")) {
                if (!Passage.transitionCache && c)
                    Passage.transitionCache = c.innerHTML;
                setTransitionCSS(passage.text);
                trans = true;
            }
        });
        if (!trans && Passage.transitionCache && c) {
            setTransitionCSS(Passage.transitionCache);
            trans = false;
            Passage.transitionCache = "";
            c.setAttribute('data-tags', tags.join(' '));
        }
    }
};

Wikifier.createInternalLink = function (place, title, callback) {
    var el = insertElement(place, 'a', title);

    if (tale.has(title)) el.className = 'internalLink';
    else el.className = 'brokenLink';

    el.onclick = function () {
        var passage = el;
        while(passage && !~passage.className.indexOf("passage")) {
            passage = passage.parentNode;
        }
        if (passage && passage.parentNode.lastChild != passage) {
            state.rewindTo(passage, true);
        }
        state.display(title, el, null, callback)
    };

    if (place) place.appendChild(el);

    return el;
};

macros.back.onclick = function(back, steps) {
    if (back) {
        var p = document.getElementById("passages").lastChild;
        while (steps > 0 && p) {
            p = p.previousSibling;
            steps--;
        }
        state.rewindTo(p);
    } else state.display(state.history[steps].passage.title);
};

function setupTagCSS() {
    var passage, tags, i, j, text = "", 
        c = document.getElementById('tagCSS'),
        openBrace = function() { text += "{"; },
        closeBrace = function() { text += "}"; },
        handler = {
            tag: null,
            keyframes: false,
            startAtrule: function(a,b) {
                this.keyframes = (a.indexOf("keyframes")>=0);
                text += a + " " + b;
            },
            startBlock: openBrace,
            endBlock: closeBrace,
            endAtrule: function() {
                this.keyframes = false;
                closeBrace();
            },
            startRuleset: function(a) { 
                var i, rules = a.join('').split(','),
                    passageRegex = /\.passage/,
                    bodyRegex = /(?:^|\s)body/;
                if (!this.keyframes) {
                    for (i = 0; i < rules.length; i++) {
                        if (rules[i].search(passageRegex)>=0) {
                            rules[i] = rules[i].replace(passageRegex,".passage[data-tags~=" + this.tag + "]");
                        }
                        else if (rules[i].search(bodyRegex)>=0) {
                            rules[i] = rules[i].replace(bodyRegex,"body[data-tags~=" + this.tag + "]");
                        }
                        else {
                            rules[i] = "body[data-tags~=" + this.tag + "] "+rules[i];
                        }
                    }
                }
                text+= rules.join(",")+"{";
            },
            declaration: function(a, b) { text+= a + " : " + b.join(" ")+";"; },
            endRuleset: closeBrace
        };
    for (i in tale.passages) {
        passage = tale.passages[i];
        if (passage && ~passage.tags.indexOf("stylesheet")) {
            for (j = 0; j < passage.tags.length; j++) {
                if (passage.tags[j] != "transition" && passage.tags[j] != "stylesheet") {
                    handler.tag = passage.tags[j];
                    parseCssStylesheet(alterCSS(passage.text),handler);
                }
            }
        }
    }
    c.styleSheet ? (c.styleSheet.cssText = text) : (c.innerHTML = text);
};

window.onload = function() {
    document.getElementById("restart").onclick=function() {
        if (confirm("Are you sure you want to restart this story?")) {
            if (typeof window.history.replaceState == "function") {
                window.history.replaceState({}, document.title, window.location.href.replace(/#.*$/,''));
            }
            else {
                window.location.hash = "";
            }
            window.location.reload()
        }
    };
    main();
    setupTagCSS();
};

