/*
**
** Sugarcane/Responsive specific code follows
**
*/
var hasPushState = !!window.history && (typeof window.history.pushState == "function");

Tale.prototype.canBookmark = function() {
    return this.canUndo() && (this.storysettings.lookup('bookmark') || !hasPushState);
};
History.prototype.init = function () {
    var a = this;
    if (!this.restore()) {
        this.display("Start", null)
    }
    if (!hasPushState) {
        this.hash = window.location.hash;
        this.interval = window.setInterval(function () {
            a.watchHash()
        }, 250)
    }
};
History.prototype.display = function (title, source, type, callback) {
    var bookmarkhref, c = tale.get(title), p = document.getElementById("passages");
    if (type != "back") {
        this.saveVariables(c, source, callback);
        if (hasPushState && tale.canUndo()) {
            if(this.history.length <= 2 && window.history.state == "") {
                window.history.replaceState(this.history, document.title);
            }
            else {
                window.history.pushState(this.history, document.title);
            }
        }
    }
    bookmarkhref = this.save();
    var e = c.render();
    if (type != "quietly") {
        if (hasTransition) {
            for(var i = 0; i < p.childNodes.length; i += 1) {
                var q = p.childNodes[i];
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
    if (tale.canUndo()) {
        if (!hasPushState && type != "back") {
            this.hash = bookmarkhref;
            window.location.hash = this.hash;
        } else if (tale.canBookmark()) {
            var bookmark = document.getElementById("bookmark");
            bookmark && (bookmark.href = bookmarkhref);
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
History.prototype.restart = function () {
    if (!hasPushState) {
        window.location.hash = "";
    } else {
        window.history.replaceState(this.history, document.title, window.location.href.replace(/#.*$/,''));
        window.location.reload();
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
        if (snapback) {
            if (!tale.lookup("tags", "bookmark").length) {
                snapback.parentNode.removeChild(snapback);
            } else snapback.onclick = Interface.showSnapback;
        }
        if (bookmark && (!tale.canBookmark() || !hasPushState)) {
            bookmark.parentNode.removeChild(bookmark);
        }
        restart && (restart.onclick = Interface.restart);
    },
    restart: function () {
        if (confirm("Are you sure you want to restart this story?")) {
            window.state.restart()
        }
    },
    showSnapback: function (a) {
        Interface.hideAllMenus();
        Interface.buildSnapback();
        Interface.showMenu(a, document.getElementById("snapbackMenu"))
    },
    buildSnapback: function () {
        var b, c = false,
            state = window.state,
            menuelem = document.getElementById("snapbackMenu");
        while (menuelem.hasChildNodes()) {
            menuelem.removeChild(menuelem.firstChild)
        }
        for(var a = state.history.length - 1; a >= 0; a--) {
            if(state.history[a].passage && state.history[a].passage.tags.indexOf("bookmark") != -1) {
                b = document.createElement("div");
                b.pos = a;
                b.onclick = function () {
                    var p = this.pos;
                    var n = state.history[p].passage.title;
                    while(p >= 0) {
                        if (state.history.length>1) {
                            state.history.shift();
                        }
                        p--;
                    }
                    state.display(n);
                };
                b.innerHTML = state.history[a].passage.excerpt();
                menuelem.appendChild(b);
                c = true
            }
        }
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
        document.onclick = Interface.hideAllMenus;
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
        while(steps >= 0 && state.history.length>1) {
            title = state.history[0].passage.title;
            state.history.shift();
            steps--;
        }
        state.display(title, null, "", (function(a) {
            if (a) return function() {
                for(var i in a) {
                    state.history[0].variables[i] = a[i];
                }
            }
        }(state.history[0].linkVars)));
    }
    else state.display(state.history[steps].passage.title);
}

window.onpopstate = function(e) {
    if (e.state && e.state.length > 0) {
        state.history = e.state;
        state.display(state.history[0].passage.title,null,"back");
    }
}
