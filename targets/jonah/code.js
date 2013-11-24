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
        el.id += "|" + (new Date).getTime();
    }
    D = tale.get(E);
    this.history.unshift({
        passage: D,
        variables: clone(this.history[0].variables)
    });
    F = D.render();
    if (A != "offscreen" && A != "quietly") {
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
    var t, E = insertElement(null, 'div', 'passage' + this.title, 'passage');
    E.style.visibility = 'hidden';
    this.setTags(E);
    this.setCSS();
    var F = insertElement(E, 'div', '', 'title', this.title);
    var D = insertElement(F, 'span', '', 'toolbar');
    for (var B = 0; B < Passage.toolbarItems.length; B++) {
        var C = insertElement(D, 'a');
        insertText(C, Passage.toolbarItems[B].label);
        C.passage = this;
        if (Passage.toolbarItems[B].href) {
            C.href = Passage.toolbarItems[B].href(E)
        }
        C.title = Passage.toolbarItems[B].tooltip;
        C.onclick = Passage.toolbarItems[B].activate
        C.div = E;
    }
    var A = insertElement(E, 'div', '', 'content');
    for (var i in prerender) {
        (typeof prerender[i] == "function") && prerender[i].call(this,A);
    }
    new Wikifier(A, this.text);
    for (i in postrender) {
        (typeof postrender[i] == "function") && postrender[i].call(this,A);
    }
    E.onmouseover = function () {
        E.className += ' selected';
    };
    E.onmouseout = function () {
        E.className = E.className.replace(' selected', '');
    };
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
Wikifier.createInternalLink = function (place, title) {
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
        state.display(title, el)
    };

    if (place) place.appendChild(el);

    return el;
};

macros.back.onclick = function(back, steps) {
    var p = document.getElementById("passages").lastChild;
    while (steps > 0 && p) {
        p = p.previousSibling;
        steps--;
    }
    state.rewindTo(p);
};
macros["return"] = {
  handler: function(a,b,c,d) { 
    throwError(a, "<<return>> has no use in Jonah", d.fullMatch());
  }
};

window.onload = function() {
    document.getElementById("restart").onclick=function() {
        if (confirm("Are you sure you want to restart this story?")) {
            window.location.reload()
        }
    };
    main();
};
