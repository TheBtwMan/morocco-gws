import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import moroccoRegions from '../../data/ma.json';
import { mockData } from '../../data/mockData';

function MoroccoMap({ selectedYear, activeFilter }) {
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', '#a8d4e6');

    const g = svg.append('g');

    const zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    const projection = d3.geoMercator()
      .fitExtent([[20, 60], [width - 20, height - 20]], moroccoRegions);

    const path = d3.geoPath().projection(projection);

    const colorScale = d3.scaleLinear()
      .domain([0, 100])
      .range(['#d73027', '#1a9850']);

    const getValue = (regionName) => {
      const region = mockData.find(r => r.name === regionName);
      if (!region) return 50;
      const filterKey = activeFilter === 'Groundwater' ? 'groundwater'
        : activeFilter === 'Surface Water' ? 'surfaceWater'
        : 'landUse';
      const yearData = region.data[filterKey];
      const years = Object.keys(yearData).map(Number);
      const closest = years.reduce((a, b) =>
        Math.abs(b - selectedYear) < Math.abs(a - selectedYear) ? b : a
      );
      return yearData[closest];
    };

    const tooltip = d3.select(tooltipRef.current);

    g.selectAll('path')
      .data(moroccoRegions.features)
      .join('path')
      .attr('d', path)
      .attr('fill', d => colorScale(getValue(d.properties.name)))
      .attr('stroke', '#c4a882')
      .attr('stroke-width', 1)
      .on('mouseover', function() {
        d3.select(this)
          .attr('stroke', '#ff0000')
          .attr('stroke-width', 2);
      })
      .on('mousemove', function(event, d) {
        const value = getValue(d.properties.name);
        tooltip
          .style('display', 'block')
          .style('left', (event.offsetX + 12) + 'px')
          .style('top', (event.offsetY - 28) + 'px')
          .html(`
            <strong>${d.properties.name}</strong><br/>
            ${activeFilter}: ${value}
          `);
      })
      .on('mouseleave', function() {
        d3.select(this)
          .attr('stroke', '#c4a882')
          .attr('stroke-width', 1);
        tooltip.style('display', 'none');
      });

  }, [selectedYear, activeFilter]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} width="100%" height="100%"></svg>
      <div ref={tooltipRef} style={{
        position: 'absolute',
        background: '#111111',
        border: '1px solid #ff0000',
        color: '#ffffff',
        padding: '8px 12px',
        borderRadius: '4px',
        fontSize: '12px',
        pointerEvents: 'none',
        display: 'none'
      }}></div>
    </div>
  );
}

export default MoroccoMap;