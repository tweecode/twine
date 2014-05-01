/*
**
** Sugarcane/Responsive specific code follows
**
*/
var hasPushState = !!window.history && (typeof window.history.pushState == "function") && (function(a) {
    // iOS Safari: setItem throws in private mode
    try {
        a.setItem("test", '1');
        a.removeItem("test");
        return true;
    } catch (e) {
        return false;
    }
}(window.sessionStorage));

Tale.prototype.canBookmark = function() {
    return this.canUndo() && !this.storysettings.lookup('hash') && (this.storysettings.lookup('bookmark',true) || !hasPushState);
};
History.prototype.init = function () {
    var a = this;
    if (!this.restore()) {
        if (tale.has("StoryInit")) {
            new Wikifier(insertElement(null, "span"), tale.get("StoryInit").text);
        }
        this.display("Start", null)
    }
    if (!hasPushState) {
        this.hash = window.location.hash;
        this.interval = window.setInterval(function () {
            a.watchHash()
        }, 250)
    }
};
hasPushState && (History.prototype.pushState = function(replace, uri) {
    window.history[replace ? "replaceState" : "pushState"]({ id: this.id, length: this.history.length }, document.title, uri);
});
History.prototype.display = function (title, source, type, callback) {
    var i, e, q, bookmark, hash, c = tale.get(title), p = document.getElementById("passages");
    if (c==null) {
        return;
    }
    if (type != "back") {
        this.saveVariables(c, source, callback);
        hash = (tale.storysettings.lookup('hash') && this.save()) || "";
        if (hasPushState && tale.canUndo()) {
            try {
                sessionStorage.setItem("Twine.History"+this.id, JSON.stringify(decompile(this.history)));
                this.pushState(this.history.length <= 2 && window.history.state == "", hash);
            } catch(e) {
                alert("Your browser couldn't save the state of the " + tale.identity() +".\n"+
                    "You may continue playing, but it will no longer be possible to undo moves from here on in.");
                tale.storysettings.undo="off";
            }
        }
    }
    this.hash = hash || this.save();
    e = c.render();
    if (type != "quietly") {
        if (hasTransition) {
            for(i = 0; i < p.childNodes.length; i += 1) {
                q = p.childNodes[i];
                q.classList.add("transition-out");
                setTimeout((function(a) { return function () {
                    if(a.parentNode) a.parentNode.removeChild(a);
                }}(q)), 1000);
            }
            e.classList.add("transition-in");
            setTimeout(function () { e.classList.remove("transition-in"); }, 1);
            e.style.visibility = "visible";
            p.appendChild(e);
        } else {
            removeChildren(p);
            p.appendChild(e);
            fade(e, {
                fade: "in"
            })
        }
    }
    else {
        p.appendChild(e);
        e.style.visibility = "visible"
    }
    tale.setPageElements();
    if (tale.canUndo()) {
        if (!hasPushState && type != "back") {
            window.location.hash = this.hash;
        } else if (tale.canBookmark()) {
            bookmark = document.getElementById("bookmark");
            bookmark && (bookmark.href = this.hash);
        }
    }
    window.scroll(0, 0)
    return e
};
History.prototype.watchHash = function () {
    if (window.location.hash != this.hash) {
        if (window.location.hash && (window.location.hash != "#")) {
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
History.prototype.loadLinkVars = function() {
    for (var c in this.history[0].linkVars) {
        this.history[0].variables[c] = clone(this.history[0].linkVars[c]);
    }
};
Passage.prototype.render = function () {
    var b = insertElement(null, 'div', 'passage' + this.title, 'passage');
    b.style.visibility = 'hidden';
    this.setTags(b);
    this.setCSS();
    insertElement(b, 'div', '', 'header');
    var a = insertElement(b, 'div', '', 'body content');
    for (var i in prerender) {
        (typeof prerender[i] == "function") && prerender[i].call(this,a);
    }
    new Wikifier(a, this.processText());
    insertElement(b, 'div', '', 'footer');
    for (i in postrender) {
        (typeof postrender[i] == "function") && postrender[i].call(this,a);
    }
    return b;
};
Passage.prototype.excerpt = function () {
    var b = this.text.replace(/<<.*?>>/g, "");
    b = b.replace(/!.*?\n/g, "");
    b = b.replace(/[\[\]\/]/g, "");
    var a = b.split("\n");
    while (a.length && a[0].length == 0) a.shift();
    var c = '';
    if (a.length == 0 || a[0].length == 0) c = this.title;
    else c = a[0].substr(0, 30) + '...';
    return c;
};
Passage.transitionCache = "";
Passage.prototype.setCSS = function() {
    var trans = false, text = "", tags = this.tags || [],
        c = document.getElementById('tagCSS'),
        c2 = document.getElementById('transitionCSS');
    
    if (c && c.getAttribute('data-tags') != tags.join(' ')) {
        tale.forEachStylesheet(tags, function(passage) {
            if (~passage.tags.indexOf("transition")) {
                if (!Passage.transitionCache && c2)
                    Passage.transitionCache = c2.innerHTML;
                setTransitionCSS(passage.text);
                trans = true;
            }
            else text += alterCSS(passage.text);
        });
        if (!trans && Passage.transitionCache && c2) {
            setTransitionCSS(Passage.transitionCache);
            trans = false;
            Passage.transitionCache = "";
        }
        c.styleSheet ? (c.styleSheet.cssText = text) : (c.innerHTML = text);
        c.setAttribute('data-tags', tags.join(' '));
    }
};

var Interface = {
    init: function () {
        var snapback = document.getElementById("snapback"),
            restart = document.getElementById("restart"),
            bookmark = document.getElementById("bookmark");
        main();
        if (!tale) {
            return;
        }
        if (snapback) {
            if (!tale.lookup("tags", "bookmark").length) {
                snapback.parentNode.removeChild(snapback);
            } else addClickHandler(snapback, Interface.showSnapback);
        }
        if (bookmark && (!tale.canBookmark() || !hasPushState)) {
            bookmark.parentNode.removeChild(bookmark);
        }
        restart && addClickHandler(restart, Interface.restart);
    },
    restart: function () {
        if (confirm("Are you sure you want to restart this " + tale.identity() + "?")) {
            state.restart()
        }
    },
    showSnapback: function (a) {
        Interface.hideAllMenus();
        Interface.buildSnapback();
        Interface.showMenu(a, document.getElementById("snapbackMenu"))
    },
    buildSnapback: function () {
        var b, c = false,
            menuelem = document.getElementById("snapbackMenu");
        while (menuelem.hasChildNodes()) {
            menuelem.removeChild(menuelem.firstChild)
        }
        for(var a = state.history.length - 1; a >= 0; a--) {
            if(state.history[a].passage && state.history[a].passage.tags.indexOf("bookmark") != -1) {
                b = document.createElement("div");
                b.pos = a;
                addClickHandler(b, function () {
                    return macros.back.onclick(true, this.pos);
                });
                b.innerHTML = state.history[a].passage.excerpt();
                menuelem.appendChild(b);
                c = true
            }
        }
        b = null
        if(!c) {
            b = document.createElement("div");
            b.innerHTML = "<i>No passages available</i>";
            document.getElementById("snapbackMenu").appendChild(b)
        }
    },
    hideAllMenus: function () {
        document.getElementById("snapbackMenu").style.display = "none"
    },
    showMenu: function (b, a) {
        if (!b) {
            b = window.event
        }
        var c = {
            x: 0,
            y: 0
        };
        if (b.pageX || b.pageY) {
            c.x = b.pageX;
            c.y = b.pageY
        } else {
            if (b.clientX || b.clientY) {
                c.x = b.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
                c.y = b.clientY + document.body.scrollTop + document.documentElement.scrollTop
            }
        }
        a.style.top = c.y + "px";
        a.style.left = c.x + "px";
        a.style.display = "block";
        addClickHandler(document, Interface.hideAllMenus);
        b.cancelBubble = true;
        if (b.stopPropagation) {
            b.stopPropagation()
        }
    }
};
window.onload = Interface.init;

macros.back.onclick = function(back, steps) {
    var title;
    if (back) {
        if (tale.canUndo()) {
            window.history.go(-steps);
            return;
        }
        while(steps-- >= 0 && state.history.length>1) {
            title = state.history[0].passage.title;
            state.history.shift();
        }
        state.loadLinkVars();
        state.saveVariables(tale.get(title));
        state.display(title, null, "back");
    }
    else {
        state.display(state.history[steps].passage.title);
    }
};

window.onpopstate = function(e) {
    var title, hist, steps, i, s = e && e.state;
    if (s && s.id && s.length != null) {
        hist = recompile(JSON.parse(sessionStorage.getItem("Twine.History"+s.id)));
        if (hist) {
            steps = hist.length-s.length;
        }
    }
    if (steps != null) {
        state.history = hist;
        // Shift the position of history to match how far back we've gone
        while(steps-- >= 0 && state.history.length>1) {
            title = state.history[0].passage.title;
            state.history.shift();
        }
        state.loadLinkVars();
        state.saveVariables(tale.get(title));
        state.display(title, null, "back");
    }
};
