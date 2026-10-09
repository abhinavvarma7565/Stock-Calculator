// charts for the simulator results page. plain svg so there is nothing to install.
// the numbers come from the json block in the page.
(function () {
  var ns = 'http://www.w3.org/2000/svg';

  function mk(tag, attrs, parent) {
    var el = document.createElementNS(ns, tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  }

  function money(v, dec) {
    var r = Math.abs(v).toFixed(dec);
    var s = Number(r).toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec});
    return (v < 0 && Number(r) > 0 ? '-' : '') + '$' + s;
  }

  // axis ticks on round numbers
  function ticks(lo, hi, n) {
    var raw = (hi - lo) / n;
    if (!(raw > 0)) return {at: [lo], step: 1};
    var p = Math.pow(10, Math.floor(Math.log10(raw)));
    var step = p * [1, 2, 2.5, 5, 10].filter(function (m) { return m * p >= raw; })[0];
    var at = [];
    for (var i = Math.ceil(lo / step - 1e-9); i * step <= hi + step * 1e-9; i++) at.push(i * step);
    return {at: at, step: step};
  }

  function decs(step) { return step >= 1 ? 0 : step >= 0.01 ? 2 : 4; }

  // the one tooltip: a heading and rows of value + name
  function makeTip(host) {
    var el = document.createElement('div');
    el.className = 'tip';
    el.hidden = true;
    el.setAttribute('role', 'status');
    host.appendChild(el);

    function add(parent, tag, cls, text) {
      var x = document.createElement(tag);
      if (cls) x.className = cls;
      if (text !== undefined) x.textContent = text;
      parent.appendChild(x);
      return x;
    }

    return {
      show: function (head, rows, x, y, w) {
        el.textContent = '';
        add(el, 'div', 'thead', head);
        rows.forEach(function (r) {
          var row = add(el, 'div', 'trow');
          if (r.key !== undefined) add(row, 'i', 'key line ' + r.key);
          add(row, 'b', '', r.value);
          add(row, 'span', '', r.name);
        });
        el.hidden = false;
        // stay inside the chart: flip to the left of the point near the right edge
        var tw = el.offsetWidth;
        el.style.left = (x + 14 + tw > w ? Math.max(0, x - 14 - tw) : x + 14) + 'px';
        el.style.top = y + 'px';
      },
      hide: function () { el.hidden = true; }
    };
  }

  // arrow keys move through the chart, same readout as hovering
  function keys(plot, count, state) {
    plot.addEventListener('keydown', function (e) {
      var i = state.cur === null ? 0 : state.cur, big = e.shiftKey ? 10 : 1;
      if (e.key === 'ArrowRight') i += big;
      else if (e.key === 'ArrowLeft') i -= big;
      else if (e.key === 'Home') i = 0;
      else if (e.key === 'End') i = count - 1;
      else return;
      e.preventDefault();
      state.pick(Math.max(0, Math.min(count - 1, i)));
    });
    plot.addEventListener('focus', function () {
      state.pick(state.cur === null ? count - 1 : state.cur);
    });
    plot.addEventListener('blur', function () { state.clear(); });
  }

  // draw once, and again whenever the width changes
  function watch(plot, draw) {
    var lastw = 0;
    function go() {
      if (plot.clientWidth === lastw) return;
      lastw = plot.clientWidth;
      draw();
    }
    new ResizeObserver(go).observe(plot);
    go();
  }

  // price fan: median, middle 50% and middle 90% of the runs, plus the break-even price
  function fan(fig, d) {
    var plot = fig.querySelector('.plot'), f = d.fan, n = f.days.length - 1;
    var tip = makeTip(plot);
    var state = {cur: null, pick: function () {}, clear: function () {}};

    function draw() {
      var old = plot.querySelector('svg');
      if (old) old.remove();
      tip.hide();

      var w = Math.max(plot.clientWidth, 280), h = w < 520 ? 260 : 320;
      var lo = Math.min(Math.min.apply(null, f.p5), d.brkeven);
      var hi = Math.max(Math.max.apply(null, f.p95), d.brkeven);
      var pad = (hi - lo) * 0.06 || hi * 0.05 || 1;
      lo -= pad;
      hi += pad;

      var yt = ticks(lo, hi, 5), ylab = yt.at.map(function (v) { return money(v, decs(yt.step)); });
      var m = {l: Math.max(44, 18 + 7 * Math.max.apply(null, ylab.map(function (s) { return s.length; }))),
               r: 14, t: 12, b: 42};
      var iw = w - m.l - m.r, ih = h - m.t - m.b;
      var xt = ticks(0, n, Math.max(3, Math.floor(iw / 90)));

      function X(i) { return m.l + iw * i / n; }
      function Y(v) { return m.t + ih * (1 - (v - lo) / (hi - lo)); }
      function line(a) {
        return a.map(function (v, i) { return (i ? 'L' : 'M') + X(i) + ',' + Y(v); }).join('');
      }
      function band(a, b) {    // forward along a, back along b
        return line(a) + b.map(function (v, i) { return 'L' + X(n - i) + ',' + Y(b[n - i]); }).join('') + 'Z';
      }

      var svg = mk('svg', {width: w, height: h, viewBox: '0 0 ' + w + ' ' + h, 'aria-hidden': 'true'});
      plot.insertBefore(svg, plot.firstChild);

      yt.at.forEach(function (v, i) {
        mk('line', {'class': 'grid', x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v)}, svg);
        mk('text', {'class': 'tick', x: m.l - 8, y: Y(v), dy: '0.32em', 'text-anchor': 'end'}, svg).textContent = ylab[i];
      });
      mk('line', {'class': 'axis', x1: m.l, x2: w - m.r, y1: h - m.b, y2: h - m.b}, svg);
      xt.at.filter(function (i) { return i % 1 === 0; }).forEach(function (i) {
        mk('text', {'class': 'tick', x: X(i), y: h - m.b + 18, 'text-anchor': 'middle'}, svg).textContent = i;
      });
      mk('text', {'class': 'atitle', x: m.l + iw / 2, y: h - 6, 'text-anchor': 'middle'}, svg).textContent = 'Trading days from today';

      mk('path', {'class': 'band', d: band(f.p5, f.p95)}, svg);
      mk('path', {'class': 'band', d: band(f.p25, f.p75)}, svg);
      mk('path', {'class': 'median', d: line(f.p50)}, svg);

      var by = Y(d.brkeven), ly = by - 7;
      if (ly < m.t + 10) ly = by + 17;    // no room above the line
      mk('line', {'class': 'be', x1: m.l, x2: w - m.r, y1: by, y2: by}, svg);
      mk('text', {'class': 'label', x: w - m.r - 4, y: ly, 'text-anchor': 'end'}, svg).textContent = 'Break-even ' + money(d.brkeven, 2);

      var g = mk('g', {visibility: 'hidden'}, svg);
      var xh = mk('line', {'class': 'xhair', y1: m.t, y2: h - m.b}, g);
      var dot = mk('circle', {'class': 'dot', r: 6}, g);

      state.pick = function (i) {
        state.cur = i;
        g.setAttribute('visibility', 'visible');
        xh.setAttribute('x1', X(i));
        xh.setAttribute('x2', X(i));
        dot.setAttribute('cx', X(i));
        dot.setAttribute('cy', Y(f.p50[i]));
        tip.show(i === 0 ? 'Today' : 'Day ' + i, [
          {key: 'none', value: money(f.p95[i], 2), name: '95th percentile'},
          {key: 'none', value: money(f.p75[i], 2), name: '75th percentile'},
          {key: '', value: money(f.p50[i], 2), name: 'Median'},
          {key: 'none', value: money(f.p25[i], 2), name: '25th percentile'},
          {key: 'none', value: money(f.p5[i], 2), name: '5th percentile'},
          {key: 'be', value: money(d.brkeven, 2), name: 'Break-even'}
        ], X(i), m.t + 6, w);
      };
      state.clear = function () {
        g.setAttribute('visibility', 'hidden');
        tip.hide();
        state.cur = null;
      };

      var hit = mk('rect', {'class': 'hit', x: m.l, y: m.t, width: iw, height: ih}, svg);
      function move(e) {
        state.pick(Math.max(0, Math.min(n, Math.round((e.clientX - svg.getBoundingClientRect().left - m.l) / iw * n))));
      }
      hit.addEventListener('pointermove', move);
      hit.addEventListener('pointerdown', move);
      hit.addEventListener('pointerleave', function (e) {
        if (e.pointerType !== 'touch' && document.activeElement !== plot) state.clear();
      });
    }

    keys(plot, n + 1, state);
    watch(plot, draw);
  }

  // histogram of net profit. every bar is a share of the runs, loss bars on the left of $0
  function hist(fig, d) {
    var plot = fig.querySelector('.plot'), e = d.bins.edges, c = d.bins.counts, nb = c.length;
    var share = c.map(function (v) { return v / d.npaths * 100; });
    var tip = makeTip(plot);
    var state = {cur: null, pick: function () {}, clear: function () {}};

    function draw() {
      var old = plot.querySelector('svg');
      if (old) old.remove();
      tip.hide();

      var w = Math.max(plot.clientWidth, 280), h = w < 520 ? 250 : 290;
      var m = {l: 46, r: 14, t: 12, b: 52};
      var iw = w - m.l - m.r, ih = h - m.t - m.b, base = h - m.b;
      var ymax = Math.max.apply(null, share) * 1.1;
      var yt = ticks(0, ymax, 4), xt = ticks(e[0], e[nb], Math.max(3, Math.floor(iw / 90)));

      function X(v) { return m.l + iw * (v - e[0]) / (e[nb] - e[0]); }
      function Y(v) { return m.t + ih * (1 - v / ymax); }

      var svg = mk('svg', {width: w, height: h, viewBox: '0 0 ' + w + ' ' + h, 'aria-hidden': 'true'});
      plot.insertBefore(svg, plot.firstChild);

      yt.at.forEach(function (v) {
        mk('line', {'class': 'grid', x1: m.l, x2: w - m.r, y1: Y(v), y2: Y(v)}, svg);
        mk('text', {'class': 'tick', x: m.l - 8, y: Y(v), dy: '0.32em', 'text-anchor': 'end'}, svg).textContent = v.toFixed(yt.step < 1 ? 1 : 0) + '%';
      });
      mk('line', {'class': 'axis', x1: m.l, x2: w - m.r, y1: base, y2: base}, svg);
      xt.at.forEach(function (v) {
        mk('text', {'class': 'tick', x: X(v), y: base + 18, 'text-anchor': 'middle'}, svg).textContent = money(v, decs(xt.step));
      });
      if (e[0] < 0 && e[nb] > 0) {
        mk('line', {'class': 'zero', x1: X(0), x2: X(0), y1: m.t, y2: base}, svg);
      }
      // direction labels, so loss vs profit is not only a colour
      mk('text', {'class': 'atitle', x: m.l, y: h - 8, 'text-anchor': 'start'}, svg).textContent = '← loss';
      mk('text', {'class': 'atitle', x: w - m.r, y: h - 8, 'text-anchor': 'end'}, svg).textContent = 'profit →';
      mk('text', {'class': 'atitle', x: m.l + iw / 2, y: h - 8, 'text-anchor': 'middle'}, svg).textContent = w < 520 ? 'Net profit' : 'Net profit after commissions and tax';

      var bars = [];
      c.forEach(function (v, i) {
        if (!v) return;
        // at most 24px wide, centred in its bin (2px gap at least), 4px rounded top, square on the baseline
        var slot = X(e[i + 1]) - X(e[i]), bw = Math.min(24, slot - 2);
        var x0 = X(e[i]) + (slot - bw) / 2, x1 = x0 + bw, y = Y(share[i]);
        var r = Math.max(0, Math.min(4, (x1 - x0) / 2, base - y));
        bars[i] = mk('path', {
          'class': 'bar ' + (e[i + 1] <= 0 ? 'loss' : 'profit'),
          d: 'M' + x0 + ',' + base + 'L' + x0 + ',' + (y + r) + 'Q' + x0 + ',' + y + ' ' + (x0 + r) + ',' + y +
             'L' + (x1 - r) + ',' + y + 'Q' + x1 + ',' + y + ' ' + x1 + ',' + (y + r) + 'L' + x1 + ',' + base + 'Z'
        }, svg);
      });

      state.pick = function (i) {
        if (state.cur !== null && bars[state.cur]) bars[state.cur].setAttribute('class', bars[state.cur].getAttribute('class').replace(' on', ''));
        state.cur = i;
        if (bars[i]) bars[i].setAttribute('class', bars[i].getAttribute('class') + ' on');
        tip.show(money(e[i], decs(xt.step)) + ' to ' + money(e[i + 1], decs(xt.step)),
                 [{value: share[i].toFixed(1) + '%', name: 'of runs'}],
                 X((e[i] + e[i + 1]) / 2), Math.max(m.t, Y(share[i]) - 64), w);
      };
      state.clear = function () {
        if (state.cur !== null && bars[state.cur]) bars[state.cur].setAttribute('class', bars[state.cur].getAttribute('class').replace(' on', ''));
        tip.hide();
        state.cur = null;
      };

      // a hit area for each bin that spans the whole column, so short bars are easy to hit
      c.forEach(function (v, i) {
        var hit = mk('rect', {'class': 'hit', x: X(e[i]), y: m.t, width: X(e[i + 1]) - X(e[i]), height: ih}, svg);
        hit.addEventListener('pointermove', function () { state.pick(i); });
        hit.addEventListener('pointerdown', function () { state.pick(i); });
        hit.addEventListener('pointerleave', function (ev) {
          if (ev.pointerType !== 'touch' && document.activeElement !== plot) state.clear();
        });
      });
    }

    keys(plot, nb, state);
    watch(plot, draw);
  }

  var data = document.getElementById('simdata');
  if (!data) return;
  var d = JSON.parse(data.textContent);
  fan(document.getElementById('fan'), d);
  hist(document.getElementById('hist'), d);
})();
