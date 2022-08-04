"use strict";

ckan.module('chartData-doughnut', function ($) {

  return {
    initialize: function($) {
      var field = this.options.field;
      var data = chartData.map(function(x) { return Object.assign({}, x); });
      var sum = data.reduce(function(sum, x) { return sum + x[field]; }, 0);
      data = data.map(function(x) {
        x.ratio = x[field] / sum;
        return x;
      });
      var chart = initChart(this.el[0], this.options.title, this.options.legend, this.options.chart, data,
        function(x) { return x[field]; },
        function(x) { return x.organization; },
        function(x) { return x[field] + " (" + (x.ratio * 100).toFixed(1) + "%)"; });
    }
  }
});

function initChart(element, title, showLegend, showChart, data, getValue, getLegend, getLabel) {
  function render() {
    d3.select(element).selectAll("*").remove();

    var leftPadding = 50,
      rightPadding = 50,
      legendWidth = leftPadding + (showLegend ? 150 : 0),
      radius = showChart ? 150 : 0,
      width = radius * 2 + legendWidth + rightPadding,
      height = 300;

    var strokeColor = d3.scaleOrdinal()
      .range(hslLerp(
        0, 60, 50, 1.0,
        360, 70, 60, 1.0,
        data.length, true));
    var fillColor = d3.scaleOrdinal()
      .range(hslLerp(
        0, 60, 70, 1.0,
        360, 70, 80, 1.0,
        data.length, true));

    var arc = d3.arc()
      .outerRadius(radius * 0.8)
      .innerRadius(radius * 0.5);

    var offsetAngle = 3 * Math.PI / 5;

    var pie = d3.pie()
      .sort(null)
      .startAngle(offsetAngle)
      .endAngle(2 * Math.PI + offsetAngle)
      .value(getValue);
    var piedata = pie(data);

    var svg = d3.select(element).append("svg")
      .attr("viewBox", "0 0 " + width + " " + height)
      .append("g")

    if(showChart) {
      var titleText = svg.append("text")
        .attr("text-anchor", "middle")
        .attr("class", "title")
        .attr("transform", "translate(" + (legendWidth + radius) + ",18)")
        .text(title)

      var sum = data.reduce(function(sum, x) { return sum + getValue(x); }, 0);
      var subText = svg.append("text")
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("class", "total")
        .style("font-size", (radius * 0.3) + "px")
        .attr("transform", "translate(" + (legendWidth + radius) + "," + (height / 2 + radius*0.125) + ")")
        .text(sum)

      var g = svg.selectAll(".arc")
        .data(piedata)
        .enter().append("g")
        .attr("transform", "translate(" + (legendWidth + radius) + "," + (height / 2 + radius * 0.1) + ")")
        .attr("class", "arc");

      g.append("path")
        .attr("d", arc)
        .style("fill", function(d, i) { return fillColor(i); })
        .style("stroke", function(d, i) { return strokeColor(i); });

      var labels = svg.selectAll(".label")
        .data(piedata)
        .enter().append("g")
        .attr("transform", "translate(" + (legendWidth + radius) + "," + (height / 2 + radius * 0.1) + ")")
        .attr("class", "label")
        .attr("visibility", function(d) { return d.value ? "visible" : "hidden"; });

      function pieAngle(d) {
        var a = (d.startAngle+d.endAngle) / 2;
        return a - (Math.floor(a/(2*Math.PI))*2*Math.PI);
      }

      labels.append("text")
        .attr("text-anchor", function(d) { return pieAngle(d) > Math.PI ? "end" : "start"; })
        .attr("x", function(d) {
          var a = pieAngle(d) - Math.PI/2;
          d.cx = Math.cos(a) * (radius * 0.65);
          return d.x = Math.cos(a) * (radius * 0.9);
        })
        .attr("y", function(d) {
          var a = pieAngle(d) - Math.PI/2;
          d.cy = Math.sin(a) * (radius * 0.65);
          // separate more on y axis to avoid overlapping labels
          let ratio = d.data.ratio ? 1 - d.data.ratio : 0;
          return d.y = Math.sin(a) * (radius * (0.9 + Math.pow(ratio, 20) * 1.0));
        })
        .text(function(d) { return getLabel(d.data); })
        .each(function(d) {
          var left = pieAngle(d) > Math.PI;
          var bbox = this.getBBox();
          d.sx = d.x + (left ? 2 : -2);
          d.ox = d.x + (left ? -1 : 1) * (bbox.width + 2);
          d.sy = d.oy = d.y + 5;
        });


      svg.append("defs").append("marker")
        .attr("id", "circ")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("refX", 3)
        .attr("refY", 3)
        .append("circle")
        .attr("cx", 3)
        .attr("cy", 3)
        .attr("r", 3);

      labels
        .append("path")
        .attr("class", "pointer")
        .style("fill", "none")
        .style("stroke", "black")
        .attr("d", function(d) {
          return "M" + d.ox + "," + d.oy + "L" + d.sx + "," + d.sy + " " + d.cx + "," + d.cy;
        });
    }
    if(showLegend) {
      var legend = svg.selectAll(".legend")
        .data(data)
        .enter().append("g")
        .attr("class", "legend")
        .attr('transform', function(d, i) {
          var h = 10 + 4;
          var x = 0;
          var y = i * h + height/2 + - data.length/2 * h ;
          return 'translate(' + x + ',' + y + ')';
        });

      legend.append('rect')
        .attr('width', 10)
        .attr('height', 10)
        .style('fill', function(d, i) { return fillColor(i); })
        .style('stroke', function(d, i) { return strokeColor(i); });

      legend.append('text')
        .attr('x', 10 + 8)
        .attr('y', 10 - 1)
        .attr('font-size', 10)
        .text(getLegend);
    }

  }

  render();
}
function hslLerp(h0, s0, l0, a0, h1, s1, l1, a1, n, striped) {
  let result = [];
  for(let i = 0; i < n; ++i) {
    let h = h0 + (h1 - h0) * i / n;
    let s = (s0 + (s1 - s0) * i / n) * (striped && i%2 ? 0.6 : 1);
    let l = (l0 + (l1 - l0) * i / n) * (striped && i%2 ? 0.9 : 1);
    let a = a0 + (a1 - a0) * i / n;
    result.push('hsla(' + h + ',' + s + '%,' + l + '%,' + a + ')')
  }
  return result;
}
