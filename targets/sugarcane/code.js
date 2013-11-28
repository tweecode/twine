/*
**
** Sugarcane/Responsive specific code follows
**
*/
History.prototype.init = function () {
    var a = this;
    if (!this.restore()) {
        this.display("Start", null)
    }
    if (!hasPushState) {
        this.hash = window.location.hash;
        this.interval = window.setInterval(function () {
            a.watchHash.apply(a)
        }, 250)
    }
};
History.prototype.display = function (title, b, type, callback) {
    var c = tale.get(title), p = document.getElementById("passages");
    if (type != "back") {
        this.history.unshift({
            passage: c,
            variables: clone(this.history[0].variables)
        });
        this.history[0].hash = this.save();
        // This must come between the history push and the state push
        // since it executes 'between' the passages.
        typeof callback == "function" && callback();
        if (hasPushState && tale.canUndo()) {
            if(this.history.length <= 2 && !window.history.state) {
                window.history.replaceState(this.history, document.title);
            }
            else {
                window.history.pushState(this.history, document.title);
            }
        }
    }
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
        e.style.visibility = "visible"
    }
    if (tale.canUndo()) {
        if (!hasPushState) {
            this.hash = this.save();
            window.location.hash = this.hash;
        } else {
            var bookmark = document.getElementById("bookmark");
            bookmark && (bookmark.href = this.save());
        }
    }
    window.scroll(0, 0)
    return e
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
Wikifier.createInternalLink = function (place, title, callback) {
    var el = insertElement(place, 'a', title);

    if (tale.has(title)) el.className = 'internalLink';
    else el.className = 'brokenLink';

    el.onclick = function () {
        state.display(title, el, null, callback)
    };

    if (place) place.appendChild(el);

    return el;
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
        if (bookmark && (!hasPushState || !tale.canUndo())) {
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
        var c = false,
            state = window.state,
            menuelem = document.getElementById("snapbackMenu");
        while (menuelem.hasChildNodes()) {
            menuelem.removeChild(menuelem.firstChild)
        }
        for(var a = state.history.length - 1; a >= 0; a--) {
            if(state.history[a].passage && state.history[a].passage.tags.indexOf("bookmark") != -1) {
                var b = document.createElement("div");
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
            var b = document.createElement("div");
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
    if (back) {
        if (tale.canUndo()) {
          window.history.go(-steps);
          return;
        }
        else while(steps >= 0) {
          if (state.history.length>1) {
            state.history.shift();
          }
          steps--;
        }
        state.display(state.history[0].passage.title);
    }
    else state.display(state.history[steps].passage.title);
}
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
