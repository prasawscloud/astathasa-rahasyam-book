(function(){
  "use strict";
  var BOOK = window.BOOK || {};
  var PAGES = BOOK.pages || [];
  var TOC = BOOK.toc || [];
  var TOTAL = BOOK.totalPages || PAGES.length;
  var $ = function(id){return document.getElementById(id);};

  function pad(n){return ("000"+n).slice(-3);}
  function imgFor(n){return "pages/page-"+pad(n)+".jpg";}
  function thumbFor(n){return "thumbs/thumb-"+pad(n)+".jpg";}
  function esc(s){return s.replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];});}
  function secIndexForPage(n){var s=0;for(var i=0;i<TOC.length;i++){if(n>=TOC[i].page)s=i;else break;}return s;}
  function store(k,v){try{localStorage.setItem(k,v);}catch(e){}}
  function load(k){try{return localStorage.getItem(k);}catch(e){return null;}}

  var NUM=/^\s*[\(]?\s*([0-9௦-௯]{1,4})\s*[.,)]\s*/;

  // ---------- render whole book ----------
  var book=$("book");
  function renderBook(){
    var html=[];
    // cover hero
    html.push('<section class="cover" id="cover">'
      +'<img class="c-img" src="'+thumbFor(1)+'" alt="cover" />'
      +'<div class="c-ta">'+esc(BOOK.title||"")+'</div>'
      +'<div class="c-en">'+esc(BOOK.titleEn||"")+'</div>'
      +'<div class="c-author">'+esc(BOOK.author||"")+'<small>'+esc(BOOK.authorEn||"")+'</small></div>'
      +'<button class="c-start" id="startBtn">படிக்கத் தொடங்கு · Start reading</button>'
      +'</section>');
    // visible contents / index
    var ci='<section class="contents" id="contents"><div class="contents-head"><h2>உள்ளடக்கம்</h2><span>Contents · '+TOC.length+' பகுதிகள்</span></div><div class="toc-grid">';
    for(var ti=0;ti<TOC.length;ti++){
      ci+='<button class="toc-card" data-sec="'+ti+'">'
        +'<span class="tc-num">'+(ti+1)+'</span>'
        +'<span class="tc-body"><span class="tc-ta">'+esc(TOC[ti].t)+'</span><span class="tc-en">'+esc(TOC[ti].e)+'</span></span>'
        +'<span class="tc-pg">ப.'+TOC[ti].page+'</span></button>';
    }
    ci+='</div></section>';
    html.push(ci);
    var curSec=-1;
    for(var i=0;i<PAGES.length;i++){
      var pg=PAGES[i];
      if(!pg.p || !pg.p.length){continue;}
      // chapter opener
      if(pg.s!==curSec){
        // only open if this page is at/after the section's start (covers first content page)
        curSec=pg.s;
        var t=TOC[curSec];
        if(t){
          html.push('<div class="chapter-open" id="sec'+curSec+'">'
            +'<div class="ch-ta">'+esc(t.t)+'</div>'
            +'<div class="ch-en">'+esc(t.e)+'</div>'
            +'<div class="ch-rule"></div></div>');
        }
      }
      // page separator + scan button
      html.push('<div class="page-sep" id="pg'+pg.n+'" data-page="'+pg.n+'">'
        +'<span>பக்கம் '+pg.n+'</span>'
        +'<button class="scan-btn" data-scan="'+pg.n+'"><svg viewBox="0 0 24 24" class="ic"><path d="M4 5h16v14H4V5zm2 2v10h12V7H6zm2 2h8v2H8V9zm0 4h8v2H8v-2z"/></svg>மூலப் படம்</button>'
        +'</div>');
      for(var j=0;j<pg.p.length;j++){
        var para=pg.p[j];
        var m=NUM.exec(para);
        if(m){
          var rest=para.slice(m[0].length);
          html.push('<p class="sutra"><span class="sn">'+esc(m[1])+'.</span> '+esc(rest)+'</p>');
        }else if(para.length<=34 && /[஀-௿]/.test(para) && !/[.?!]$/.test(para)){
          html.push('<p class="heading">'+esc(para)+'</p>');
        }else{
          html.push('<p>'+esc(para)+'</p>');
        }
      }
    }
    book.innerHTML=html.join("");
  }

  // ---------- navigation ----------
  function goToPage(n,flash){
    var el=$("pg"+n) || document.querySelector('[data-page="'+n+'"]');
    if(!el){ // find nearest existing page >= n
      for(var k=n;k<=TOTAL;k++){el=$("pg"+k);if(el)break;}
    }
    if(el){
      var y=el.getBoundingClientRect().top+window.pageYOffset-64;
      window.scrollTo({top:y,behavior:flash?"smooth":"auto"});
      if(flash){var p=el.nextElementSibling;if(p){p.classList.add("target-flash");setTimeout(function(){p.classList.remove("target-flash");},1700);}}
    }
  }
  function goToSection(i){var t=TOC[i];if(t)goToPage(t.page,true);}

  // ---------- status + progress + current chapter ----------
  var statusChapter=$("statusChapter"),statusPage=$("statusPage"),progressBar=$("progressBar");
  var sepEls=[];
  function indexSeps(){sepEls=Array.prototype.slice.call(document.querySelectorAll(".page-sep"));}
  var ticking=false;
  function onScroll(){
    if(ticking)return;ticking=true;
    requestAnimationFrame(function(){
      ticking=false;
      var doc=document.documentElement;
      var sc=window.pageYOffset, h=doc.scrollHeight-doc.clientHeight;
      var pct=h>0?Math.min(100,Math.max(0,sc/h*100)):0;
      progressBar.style.width=pct+"%";
      // find current page (last sep above mid-viewport)
      var mid=120, cur=null;
      for(var i=0;i<sepEls.length;i++){
        if(sepEls[i].getBoundingClientRect().top<=mid){cur=sepEls[i];}else break;
      }
      if(cur){
        var n=+cur.getAttribute("data-page");
        var si=secIndexForPage(n);
        statusChapter.textContent=TOC[si]?TOC[si].t:"";
        statusPage.textContent="பக்கம் "+n+" / "+TOTAL;
        store("ar_pos", n);
        markTocCurrent(si);
      }
    });
  }

  // ---------- TOC ----------
  var tocList=$("tocList");
  function buildTOC(){
    var h="";
    for(var i=0;i<TOC.length;i++){
      h+='<button class="toc-item" data-sec="'+i+'">'
        +'<span class="toc-num">'+(i+1)+'</span>'
        +'<span class="toc-txt"><span class="toc-ta">'+esc(TOC[i].t)+'</span><span class="toc-en">'+esc(TOC[i].e)+'</span></span>'
        +'<span class="toc-pg">ப.'+TOC[i].page+'</span></button>';
    }
    tocList.innerHTML=h;
    tocList.querySelectorAll(".toc-item").forEach(function(b){
      b.onclick=function(){closeTOC();goToSection(+b.dataset.sec);};
    });
  }
  var curTocSec=-1;
  function markTocCurrent(si){
    if(si===curTocSec)return;curTocSec=si;
    tocList.querySelectorAll(".toc-item").forEach(function(b){b.classList.toggle("is-current",+b.dataset.sec===si);});
  }
  function openTOC(){$("tocDrawer").hidden=false;}
  function closeTOC(){$("tocDrawer").hidden=true;}
  $("tocBtn").onclick=openTOC;$("tocClose").onclick=closeTOC;$("tocScrim").onclick=closeTOC;
  $("brandBtn").onclick=function(){window.scrollTo({top:0,behavior:"smooth"});};

  // ---------- scan lightbox ----------
  var scanModal=$("scanModal"),scanImg=$("scanImg"),scanLabel=$("scanLabel");
  function openScan(n){scanLabel.textContent="மூலப் பக்கம் "+n+" · Original page "+n;scanImg.src=imgFor(n);scanModal.hidden=false;$("scanBody").scrollTop=0;}
  function closeScan(){scanModal.hidden=true;scanImg.src="";}
  $("scanClose").onclick=closeScan;
  scanModal.addEventListener("click",function(e){if(e.target===scanModal||e.target===$("scanBody"))closeScan();});
  book.addEventListener("click",function(e){
    var b=e.target.closest(".scan-btn");if(b){openScan(+b.dataset.scan);return;}
    var c=e.target.closest(".toc-card");if(c){goToSection(+c.dataset.sec);return;}
    var s=e.target.closest("#startBtn");if(s){goToPage(1,true);}
  });

  // ---------- display (Aa) ----------
  var aaPop=$("aaPop");
  $("aaBtn").onclick=function(e){e.stopPropagation();aaPop.hidden=!aaPop.hidden;syncAa();};
  document.addEventListener("click",function(e){if(!aaPop.hidden && !aaPop.contains(e.target) && e.target!==$("aaBtn") && !$("aaBtn").contains(e.target))aaPop.hidden=true;});
  var fontPct=parseInt(load("ar_fontpct")||"100",10);
  function applyFont(){document.documentElement.style.setProperty("--read-size",(1.16*fontPct/100).toFixed(3)+"rem");$("fontLabel").textContent=fontPct+"%";store("ar_fontpct",fontPct);}
  $("fontUp").onclick=function(){fontPct=Math.min(180,fontPct+10);applyFont();};
  $("fontDown").onclick=function(){fontPct=Math.max(75,fontPct-10);applyFont();};
  function setAttr(name,val,key){document.body.setAttribute(name,val);store(key,val);syncAa();}
  aaPop.querySelectorAll(".theme-chip").forEach(function(b){b.onclick=function(){setAttr("data-theme",b.dataset.theme,"ar_theme");};});
  aaPop.querySelectorAll(".font-chip").forEach(function(b){b.onclick=function(){setAttr("data-font",b.dataset.font,"ar_font");};});
  aaPop.querySelectorAll(".width-chip").forEach(function(b){b.onclick=function(){setAttr("data-width",b.dataset.width,"ar_width");};});
  function syncAa(){
    aaPop.querySelectorAll(".theme-chip").forEach(function(b){b.classList.toggle("sel",b.dataset.theme===document.body.getAttribute("data-theme"));});
    aaPop.querySelectorAll(".font-chip").forEach(function(b){b.classList.toggle("sel",b.dataset.font===document.body.getAttribute("data-font"));});
    aaPop.querySelectorAll(".width-chip").forEach(function(b){b.classList.toggle("sel",b.dataset.width===document.body.getAttribute("data-width"));});
  }

  // ---------- search ----------
  var searchOverlay=$("searchOverlay"),searchInput=$("searchInput"),searchResults=$("searchResults"),searchCount=$("searchCount"),searchHint=$("searchHint");
  function openSearch(){searchOverlay.hidden=false;setTimeout(function(){searchInput.focus();},30);}
  function closeSearch(){searchOverlay.hidden=true;}
  $("searchBtn").onclick=openSearch;$("searchClose").onclick=closeSearch;
  searchOverlay.addEventListener("click",function(e){if(e.target===searchOverlay)closeSearch();});
  var pageText=PAGES.map(function(p){return (p.p||[]).join(" ");});
  function snippet(text,q){
    var i=text.toLowerCase().indexOf(q);
    if(i<0)return esc(text.slice(0,120));
    var s=Math.max(0,i-42),e=Math.min(text.length,i+q.length+78);
    return (s>0?"… ":"")+esc(text.slice(s,i))+"<mark>"+esc(text.slice(i,i+q.length))+"</mark>"+esc(text.slice(i+q.length,e))+(e<text.length?" …":"");
  }
  var sTimer,activeIdx=-1;
  function runSearch(){
    var raw=searchInput.value.trim(),q=raw.toLowerCase();activeIdx=-1;
    if(!q){searchHint.style.display="";searchResults.innerHTML="";searchResults.appendChild(searchHint);searchCount.textContent="";return;}
    searchHint.style.display="none";
    var res=[];
    for(var k=0;k<pageText.length;k++){if(pageText[k].toLowerCase().indexOf(q)>=0){res.push(PAGES[k].n);if(res.length>=400)break;}}
    searchCount.textContent=res.length?(res.length>=400?"400+":res.length)+" பக்கம்":"";
    if(!res.length){searchResults.innerHTML='<div class="search-empty">முடிவு இல்லை · No matches</div>';return;}
    var h="";
    for(var r=0;r<res.length;r++){var n=res[r];h+='<button class="result" data-n="'+n+'"><span class="result-no">'+n+'<small>பக்கம்</small></span><span class="result-snip">'+snippet(pageText[n-1],q)+'</span></button>';}
    searchResults.innerHTML=h;
    searchResults.querySelectorAll(".result").forEach(function(el){el.onclick=function(){closeSearch();goToPage(+el.dataset.n,true);};});
  }
  searchInput.addEventListener("input",function(){clearTimeout(sTimer);sTimer=setTimeout(runSearch,140);});
  searchInput.addEventListener("keydown",function(e){
    var items=searchResults.querySelectorAll(".result");
    if(e.key==="ArrowDown"){e.preventDefault();activeIdx=Math.min(items.length-1,activeIdx+1);}
    else if(e.key==="ArrowUp"){e.preventDefault();activeIdx=Math.max(0,activeIdx-1);}
    else if(e.key==="Enter"){(items[activeIdx]||items[0])&&(items[activeIdx]||items[0]).click();return;}
    else return;
    items.forEach(function(it,i){it.classList.toggle("is-active",i===activeIdx);if(i===activeIdx)it.scrollIntoView({block:"nearest"});});
  });

  // ---------- keyboard ----------
  document.addEventListener("keydown",function(e){
    if(!searchOverlay.hidden){if(e.key==="Escape")closeSearch();return;}
    if(!scanModal.hidden){if(e.key==="Escape")closeScan();return;}
    if(!$("tocDrawer").hidden){if(e.key==="Escape")closeTOC();return;}
    var tag=(e.target.tagName||"").toLowerCase();if(tag==="input")return;
    if(e.key==="/"){e.preventDefault();openSearch();}
    else if(e.key==="t"||e.key==="T"){openTOC();}
    else if(e.key==="Escape"){aaPop.hidden=true;}
  });

  // ---------- restore prefs ----------
  (function(){
    var th=load("ar_theme");if(!th&&window.matchMedia&&matchMedia("(prefers-color-scheme:dark)").matches)th="night";
    if(th)document.body.setAttribute("data-theme",th);
    var fn=load("ar_font");if(fn)document.body.setAttribute("data-font",fn);
    var wd=load("ar_width");if(wd)document.body.setAttribute("data-width",wd);
    applyFont();
  })();

  // ---------- init ----------
  function init(){
    renderBook();buildTOC();indexSeps();
    window.addEventListener("scroll",onScroll,{passive:true});
    onScroll();
    var m=location.hash.match(/p=(\d+)/), saved=load("ar_pos");
    if(m){goToPage(parseInt(m[1],10),true);}
    else if(saved&&+saved>1){goToPage(parseInt(saved,10),false);}
    setTimeout(function(){$("boot").classList.add("hide");},400);
  }
  if(!PAGES.length){$("boot").innerHTML='<p style="font-family:var(--ta-sans)">தரவு ஏற்ற முடியவில்லை — data/book.js.</p>';}
  else{init();}
})();
