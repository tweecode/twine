/*
**
** Jonah specific code follows
**
*/
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
History.prototype.display = function (E, C, A) {
    var el, D, F, p = document.getElementById("passages");
    if (el = document.getElementById("passage" + E)) {
        el.id += (new Date).getTime();
    }
    D = tale.get(E);
    this.history.unshift({
        passage: D,
        variables: clone(this.history[0].variables)
    });
    F = D.render();
    if (A != "offscreen" && A != "quietly") {
        if (hasTransition) {
            for(var i = 0; i < p.childNodes.length; i += 1) {
                var q = p.childNodes[i];
                q.classList.add("transition-out");
            }
            F.classList.add("transition-in");
            setTimeout(function () {
                F.classList.remove("transition-in");
            }, 1);
            F.style.visibility = "visible"
            p.appendChild(F);
        } else {
            p.appendChild(F);
            fade(F, {
                fade: "in"
            });
        }
        scrollWindowTo(F);
    }
    else {
        p.appendChild(F);
        F.style.visibility = "visible"
    }
    return F
};
History.prototype.rewindTo = function (C) {
    var B = this;
    fade(document.getElementById("passages"), {
        fade: "out",
        onComplete: A
    });

    function A() {
        var p = document.getElementById("passages");
        while (p.lastChild != C.div) {
            p.removeChild(p.lastChild);
            B.history.shift();
        }
        B.history[0].variables = clone(B.history[1].variables);
        C.passage.reset();
        var E = C.div.querySelector(".body");
        if(E) {
            removeChildren(E);
            new Wikifier(E, C.passage.text);
        }
        fade(document.getElementById("passages"), {
            fade: "in"
        })
    }
};
Passage.prototype.render = function () {
    var t, E = insertElement(null, 'div', 'passage' + this.title, 'passage');
    E.style.visibility = 'hidden';
    this.setTags(E);
    this.setCSS();
    var F = insertElement(E, 'div', '', 'title', this.title);
    var D = insertElement(F, 'span', '', 'toolbar');
    for (var B = 0; B < Passage.toolbarItems.length; B++) {
        var C = insertElement(D, 'a');
        insertText(C, Passage.toolbarItems[B].label(E));
        C.passage = this;
        if (Passage.toolbarItems[B].href) {
            C.href = Passage.toolbarItems[B].href(E)
        } else {
            C.href = 'javascript:void(0)';
        }
        C.title = Passage.toolbarItems[B].tooltip(E);
        C.onclick = Passage.toolbarItems[B].activate
    }
    var A = insertElement(E, 'div', '', 'body');
    new Wikifier(A, this.text);
    E.onmouseover = function () {
        E.className += ' selected';
    };
    E.onmouseout = function () {
        E.className = E.className.replace(' selected', '');
    };
    var rewind = E.querySelector(".toolbar a:last-child");
    rewind && (rewind.div = E);
    return E
};
Passage.prototype.reset = function () {
    this.text = this.initialText
};
Passage.toolbarItems = [{
    label: function () {
        return "bookmark"
    },
    tooltip: function () {
        return "Bookmark this point in the story"
    },
    href: function (A) {
        return (state.save(A))
    },
    activate: function () {}
}, {
    label: function () {
        return "rewind to here"
    },
    tooltip: function () {},
    activate: function () {
        state.rewindTo(this)
    }
}];

version.extensions.choiceMacro = {
    major: 1,
    minor: 2,
    revision: 0
};
macros.choice = {
    handler: function (A, C, D) {
        var B = document.createElement("a");
        B.href = "javascript:void(0)";
        B.className = "internalLink choice";
        if (D[1]) {
            B.innerHTML = D[1]
        } else {
            B.innerHTML = D[0]
        }
        B.onclick = function () {
            macros.choice.activate(B, D[0])
        };
        A.appendChild(B)
    },
    activate: function (E, A) {
        var H = E.parentNode;
        while (H.className.indexOf("body") == -1) {
            H = H.parentNode
        }
        var G = H.parentNode.id.substr(7),
            B = H.getElementsByTagName("a"),
            F = [];
        for (var C = 0; C < B.length; C++) {
            if ((B[C] != E) && (B[C].className.indexOf("choice") != -1)) {
                var D = document.createElement("span");
                D.innerHTML = B[C].innerHTML;
                D.className = "disabled";
                B[C].parentNode.insertBefore(D, B[C].nextSibling);
                F.push(B[C])
            }
        }
        for (var C = 0; C < F.length; C++) {
            F[C].parentNode.removeChild(F[C])
        }
        tale.get(G).text = "<html>" + H.childNodes[0].innerHTML + "</html>";
        state.display(A, E)
    }
};
version.extensions.backMacro={major:1,minor:0,revision:0};
macros.back={handler:function(a,b,c){return}};
version.extensions.returnMacro={major:1,minor:0,revision:0};
macros.return={handler:function(a,b,c){return}};

window.onload = function() {
    document.getElementById("restart").onclick=function() {
        if (confirm("Are you sure you want to restart this story?")) {
            window.location.reload()
        }
    };
    main();
};
