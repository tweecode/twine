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
History.prototype.display = function (d, b, a) {
    var c = tale.get(d), p = document.getElementById("passages");
    if (a != "back") {
        this.history.unshift({
            passage: c,
            variables: clone(this.history[0].variables)
        });
        this.history[0].hash = this.save();
        if (hasPushState) {
            if(this.history.length <= 2 && window.history.state === null) {
                window.history.replaceState(this.history, document.title);
            }
            else {
                window.history.pushState(this.history, document.title);
            }
        }
    }
    var e = c.render();
    if (a != "quietly") {
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
            e.style.visibility = "visible"
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
    if (!hasPushState) {
        this.hash = this.save();
        window.location.hash = this.hash;
    } else {
        var bookmark = document.getElementById("bookmark");
        bookmark && (bookmark.href = this.save());
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
    var a = insertElement(b, 'div', '', 'content');
    for (var i in prerender) {
        (typeof prerender[i] == "function") && prerender[i].call(this,a);
    }
    new Wikifier(a, this.text);
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
Wikifier.createInternalLink = function (place, title) {
    var el = insertElement(place, 'a', title);

    if (tale.has(title)) el.className = 'internalLink';
    else el.className = 'brokenLink';

    el.onclick = function () {
        state.display(title, el)
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
        if (bookmark && !hasPushState) {
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

version.extensions.backMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros['back'] = {
  labeltext: '&#171; back',
  handler: function (a, b, e) {
    var d = "",
        labeltouse = this.labeltext,
        steps = 1,
        stepsParam = e.indexOf("steps"),
        stepsParam2 = "",
        labelParam,    c, el;
    // Steps parameter
    if (stepsParam>0) {
        stepsParam2 = e[stepsParam-1];
        if (stepsParam2[0] =='$') {
            try {
                stepsParam2=eval(Wikifier.parse(stepsParam2));
            } catch (r) {
                throwError(a, b+"Macro bad expression: " + r.message)
                return;
            }
        }
        // Previously, trying to go back more steps than were present in the
        // history would silently revert to just 1 step. 
        // Instead, let's just go back to the start.
        steps = +stepsParam2;
        if (steps >= state.history.length-1) {
          steps = state.history.length-2;
        }
        d = state.history[steps].passage.title;
        e.splice(stepsParam-1,2);
    }
    // Label parameter
    labelParam = e.indexOf("label");
    if (labelParam == -1) {
        labelParam = e.indexOf("labeldefault");
    }
    if (labelParam >-1) {
        if (!e[labelParam+1]) {
            throwError(a, e[labelParam] + 'keyword needs an additional label parameter');
            return;
        }
        labeltouse = e[labelParam+1];
        if (e[labelParam] == 'labeldefault') this.labeltext = labeltouse;
        e.splice(labelParam,2);
    }
    // What's left is the passage name parameter
    if (!d) {
      if(e[0]) {
        if (e[0].charAt(0)=='$') {
            try {
                e=eval(Wikifier.parse(e[0]));
            } catch (r) {
                throwError(a, b+"Macro bad expression: " + r.message)
                return;
            }
        } 
        else {
            e = e[0];
        }
        if (tale.get(e).id == undefined) {
          throwError(a, "The " + e + " passage does not exist");
          return;
        }
        for(c = 0; c < state.history.length; c++) {
            if(state.history[c].passage.title == e) {
                d = e;
                steps = c;
                break;
            }
        }
      }
      else {
        d = state.history[1].passage.title;
      }
    }
    if (d==undefined) {
      return;
    } else {
      el = document.createElement("a");
      el.className = "return";
      el.onclick = function () {
        if (b=="back") {
            if (hasPushState) {
              window.history.back();
              return;
            }
            else while(steps >= 0) {
              if (state.history.length>1) {
                state.history.shift();
              }
              steps--;
            }
        }
        state.display(d);
      };
      el.href = "javascript:void(0)";
      el.innerHTML = labeltouse;
      a.appendChild(el);
    }
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
    macros['back'].handler.call(this,a,b,e);
  }
};
version.extensions.choiceMacro = {
    major: 2,
    minor: 0,
    revision: 0
};
macros.choice = {
    handler: function (A, C, D) {
        var passage, id, text = D[1] || D[0],
            clicked = state.history[0].variables["choice clicked"] 
                || (state.history[0].variables["choice clicked"] = {}),
        // Get enclosing passage name
        passage = A;
        while(passage && !~passage.className.indexOf("passage")) {
            passage = passage.parentNode;
        }
        // Get ID of the "choice clicked" entry
        id = (passage && passage.id.replace(/\|.*$/,'') + "|" + text);
        
        if (id && clicked[id]) {
            insertElement(A, "span", null, "disabled", text); 
        }
        else {
            B = Wikifier.createInternalLink(A, D[0]);
            B.innerHTML = text;
            B.className += " " + C;
            B.onclick = (function(B, onclick) { return function() {
                onclick();
                clicked[id] = true;
                B.outerHTML = "<span class=disabled>" + B.innerHTML + "</span>";
            }}(B, B.onclick));
        }
    }
};