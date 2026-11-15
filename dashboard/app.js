'use strict';

const $ = (id) => document.getElementById(id);
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const CATEGORY_LABELS = {
  muito_seco: 'Very dry',
  seco: 'Dry',
  normal: 'Normal',
  chuvoso: 'Wet',
  muito_chuvoso: 'Very wet',
  referencia_insuficiente: 'Insufficient reference',
};
const CATEGORY_CLASSES = {
  muito_seco: 'category-very-dry',
  seco: 'category-dry',
  normal: 'category-normal',
  chuvoso: 'category-wet',
  muito_chuvoso: 'category-very-wet',
};
const SERIES_COLORS = { primary: '#FFFF00', comparison: '#614AD3' };
const fmt = (value, digits = 1) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
  ? Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
  : '—';
const signed = (value, digits = 1) => {
  if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—';
  const parsed = Number(Number(value).toFixed(digits));
  const rounded = Object.is(parsed, -0) ? 0 : parsed;
  return `${rounded > 0 ? '+' : ''}${fmt(rounded, digits)}`;
};
const pformat = (value) => !Number.isFinite(Number(value))
  ? '—'
  : Number(value) < 0.001 ? '<0.001' : fmt(value, 3);
const valid = (value) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);

let data;
let current;
let currentStateRows = [];
let dailyByState = null;
let dailyClimatology = null;

function svg(content, label, viewBox = '0 0 1000 300') {
  return `<svg viewBox="${viewBox}" role="img" aria-label="${esc(label)}" xmlns="http://www.w3.org/2000/svg">${content}</svg>`;
}

function text(x, y, value, extra = '') {
  return `<text x="${x}" y="${y}" class="axis-label" ${extra}>${esc(value)}</text>`;
}

function makeSelect(select, states, selected) {
  select.replaceChildren(...states.map((state) => {
    const option = document.createElement('option');
    option.value = state.uf;
    option.textContent = `${state.name} (${state.uf})`;
    option.selected = state.uf === selected;
    return option;
  }));
}

function yearBounds() {
  const completeYears = data.states.flatMap((state) => state.annual
    .filter((row) => row.complete && valid(row.annual_total_mm))
    .map((row) => row.year));
  if (!completeYears.length) throw new Error('No complete annual precipitation records are available.');
  return { first: Math.min(...completeYears), last: Math.max(...completeYears) };
}

function setInputRange(input, frequency, startValue, min, max) {
  input.type = frequency === 'annual' ? 'number' : frequency === 'monthly' ? 'month' : 'date';
  input.step = '1';
  input.min = min;
  input.max = max;
  input.value = startValue;
}

function validInputValue(value, frequency) {
  const pattern = frequency === 'annual'
    ? /^\d{4}$/
    : frequency === 'monthly'
      ? /^\d{4}-\d{2}$/
      : /^\d{4}-\d{2}-\d{2}$/;
  return pattern.test(value);
}

function dateValueFor(frequency, year, month = 1, day = 1) {
  if (frequency === 'annual') return String(year);
  if (frequency === 'monthly') return `${year}-${String(month).padStart(2, '0')}`;
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function configurePeriodInputs(frequency) {
  const bounds = yearBounds();
  const lastYear = bounds.last;
  let startMin;
  let startDefault;
  let endDefault;
  let min;
  let max;

  if (frequency === 'annual') {
    min = String(bounds.first);
    max = String(lastYear);
    startDefault = min;
    endDefault = max;
    startMin = min;
  } else if (frequency === 'monthly') {
    min = `${data.reference.start_year}-01`;
    max = `${data.reference.end_year}-12`;
    startDefault = min;
    endDefault = max;
    startMin = min;
  } else {
    min = `${data.reference.start_year}-01-01`;
    max = `${data.reference.end_year}-12-31`;
    startDefault = min;
    endDefault = max;
    startMin = min;
  }

  for (const [startId, endId, initialStart, initialEnd] of [
    ['period-start', 'period-end', startDefault, endDefault],
    [
      'compare-period-start',
      'compare-period-end',
      frequency === 'annual'
        ? String(bounds.first)
        : dateValueFor(frequency, bounds.first, frequency === 'monthly' ? 1 : 1, 1),
      frequency === 'annual'
        ? String(Math.min(bounds.first + 8, lastYear))
        : dateValueFor(frequency, Math.min(bounds.first + 8, lastYear), 12, 31),
    ],
  ]) {
    const start = $(startId);
    const end = $(endId);
    const priorStart = start.value;
    const priorEnd = end.value;
    setInputRange(start, frequency, initialStart, startMin, max);
    setInputRange(end, frequency, initialEnd, min, max);
    if (validInputValue(priorStart, frequency) && priorStart >= min && priorStart <= max) start.value = priorStart;
    if (validInputValue(priorEnd, frequency) && priorEnd >= min && priorEnd <= max) end.value = priorEnd;
  }
}

function parsePeriod(value, frequency, endOfPeriod = false) {
  if (frequency === 'annual') {
    return endOfPeriod ? `${value}-12-31` : `${value}-01-01`;
  }
  if (frequency === 'monthly') {
    if (!endOfPeriod) return `${value}-01`;
    const [year, month] = value.split('-').map(Number);
    return `${value}-${String(new Date(Date.UTC(year, month, 0)).getUTCDate()).padStart(2, '0')}`;
  }
  return value;
}

function selectedRange(prefix = '') {
  const frequency = $('frequency').value;
  const start = $(`${prefix}period-start`).value;
  const end = $(`${prefix}period-end`).value;
  return {
    start: parsePeriod(start, frequency, false),
    end: parsePeriod(end, frequency, true),
    startInput: start,
    endInput: end,
  };
}

function normalizeRanges() {
  for (const prefix of ['', 'compare-']) {
    const start = $(`${prefix}period-start`);
    const end = $(`${prefix}period-end`);
    if (start.value && end.value && start.value > end.value) end.value = start.value;
  }
}

function dateFromParts(year, month, day = 1) {
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function stampForRow(row, frequency) {
  if (frequency === 'annual') return Date.UTC(Number(row.year), 6, 1);
  if (frequency === 'monthly') return Date.UTC(Number(row.year), Number(row.month) - 1, 15);
  return Date.parse(`${row.date}T00:00:00Z`);
}

function getSeriesRows(state, frequency, range) {
  let rows;
  if (frequency === 'daily') {
    if (!dailyByState) return [];
    const dataRows = dailyByState.get(state.uf);
    if (!dataRows) return [];
    rows = [];
    const from = Number(range.start.replaceAll('-', ''));
    const through = Number(range.end.replaceAll('-', ''));
    for (let index = 0; index < dataRows.dates.length; index += 1) {
      const dateCode = dataRows.dates[index];
      if (dateCode < from || dateCode > through) continue;
      const date = String(dateCode).padStart(8, '0');
      rows.push({
        date: `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`,
        value: dataRows.values[index],
        stamp: Date.parse(`${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}T00:00:00Z`),
      });
    }
    return rows;
  }

  rows = frequency === 'annual' ? state.annual : state.monthly;
  return rows.filter((row) => {
    const amount = frequency === 'annual' ? row.annual_total_mm : row.precip_mm;
    if (!row.complete || !valid(amount)) return false;
    const date = frequency === 'annual'
      ? `${row.year}-07-01`
      : `${row.year}-${String(row.month).padStart(2, '0')}-15`;
    return date >= range.start && date <= range.end;
  }).map((row) => ({
    ...row,
    date: frequency === 'annual'
      ? dateFromParts(row.year, 7, 1)
      : dateFromParts(row.year, row.month, 15),
    value: Number(frequency === 'annual' ? row.annual_total_mm : row.precip_mm),
    stamp: stampForRow(row, frequency),
  }));
}

function buildSelectedSeries() {
  const frequency = $('frequency').value;
  const primaryRange = selectedRange();
  const comparisonRange = $('compare-period-enabled').checked ? selectedRange('compare-') : null;
  const definitions = [{
    state: current,
    range: primaryRange,
    color: SERIES_COLORS.primary,
    dash: false,
    label: `${current.name} · selected period`,
  }];
  const comparisonState = $('compare-state-enabled').checked
    ? data.states.find((state) => state.uf === $('compare-state').value)
    : null;
  if (comparisonState) {
    definitions.push({
      state: comparisonState,
      range: primaryRange,
      color: SERIES_COLORS.comparison,
      dash: false,
      label: `${comparisonState.name} · selected period`,
    });
  }
  if (comparisonRange) {
    definitions.push({
      state: current,
      range: comparisonRange,
      color: SERIES_COLORS.primary,
      dash: true,
      label: `${current.name} · comparison period`,
    });
    if (comparisonState) {
      definitions.push({
        state: comparisonState,
        range: comparisonRange,
        color: SERIES_COLORS.comparison,
        dash: true,
        label: `${comparisonState.name} · comparison period`,
      });
    }
  }
  return definitions.map((definition) => ({
    ...definition,
    rows: getSeriesRows(definition.state, frequency, definition.range),
  }));
}

function average(rows) {
  if (!rows.length) return null;
  return rows.reduce((sum, row) => sum + row.value, 0) / rows.length;
}

function periodTotal(rows) {
  return rows.reduce((sum, row) => sum + row.value, 0);
}

function climatologyFor(state, month) {
  return state.climate.find((row) => Number(row.month) === month);
}

function selectedPeriodExpected(state, range, frequency, observedRows) {
  if (frequency === 'daily') {
    if (!dailyClimatology) return null;
    const means = dailyClimatology.get(state.uf);
    if (!means) return null;
    let expected = 0;
    let count = 0;
    for (const row of observedRows) {
      const key = row.date.slice(5);
      const mean = means.get(key);
      if (valid(mean)) {
        expected += mean;
        count += 1;
      }
    }
    return count ? expected : null;
  }

  if (frequency === 'monthly') {
    let expected = 0;
    let count = 0;
    for (const row of state.monthly) {
      const date = dateFromParts(row.year, row.month, 15);
      if (!row.complete || date < range.start || date > range.end) continue;
      const climate = climatologyFor(state, Number(row.month));
      if (valid(climate?.mean_mm)) {
        expected += Number(climate.mean_mm);
        count += 1;
      }
    }
    return count ? expected : null;
  }

  const trendMean = Number(state.trend.mean_annual_mm);
  if (!valid(trendMean)) return null;
  return observedRows.length ? trendMean * observedRows.length : null;
}

function renderIndicators() {
  const frequency = $('frequency').value;
  const annualTotal = current.annual.find((row) => Number(row.year) === Number($('reference-year')?.value));
  const climate = current.climate.filter((row) => valid(row.mean_mm));
  const monthlyAverage = average(climate.map((row) => ({ value: Number(row.mean_mm) })));
  const wettest = climate.reduce((best, row) => Number(row.mean_mm) > Number(best.mean_mm) ? row : best, climate[0]);
  const driest = climate.reduce((best, row) => Number(row.mean_mm) < Number(best.mean_mm) ? row : best, climate[0]);
  const range = selectedRange();
  const visibleRows = getSeriesRows(current, frequency, range);
  const actual = periodTotal(visibleRows);
  const expected = selectedPeriodExpected(current, range, frequency, visibleRows);
  const anomaly = expected === null ? null : actual - expected;
  const anomalyPercent = expected ? anomaly / expected * 100 : null;
  const stateAnnual = current.annual.filter((row) => row.complete && valid(row.annual_total_mm));

  $('annual-total').textContent = annualTotal?.complete && valid(annualTotal.annual_total_mm)
    ? `${fmt(Number(annualTotal.annual_total_mm))} mm`
    : '—';
  $('annual-period').textContent = annualTotal?.complete
    ? `Complete annual total · ${annualTotal.year}`
    : `${annualTotal?.year ?? 'Selected year'} · complete annual total unavailable`;
  $('monthly-average').textContent = monthlyAverage === null ? '—' : `${fmt(monthlyAverage)} mm`;
  $('monthly-average-note').textContent = `Average of ${climate.length} calendar-month climatologies`;
  $('wettest-month').textContent = wettest ? MONTHS[Number(wettest.month) - 1] : '—';
  $('wettest-month-note').textContent = wettest ? `${fmt(Number(wettest.mean_mm))} mm historical average` : 'No monthly reference available';
  $('driest-month').textContent = driest ? MONTHS[Number(driest.month) - 1] : '—';
  $('driest-month-note').textContent = driest ? `${fmt(Number(driest.mean_mm))} mm historical average` : 'No monthly reference available';
  $('period-anomaly').textContent = anomaly === null
    ? '—'
    : `${signed(anomaly)} mm`;
  $('period-anomaly').classList.toggle('negative', anomaly !== null && anomaly < 0);
  $('period-anomaly-note').textContent = anomaly === null
    ? 'No historical reference for this selection'
    : `${range.startInput}–${range.endInput} · ${signed(anomalyPercent)}% vs. climatology`;

  return stateAnnual;
}

function dateLabel(date, frequency) {
  if (frequency === 'annual') return date.slice(0, 4);
  if (frequency === 'monthly') {
    const [year, month] = date.split('-');
    return `${MONTHS[Number(month) - 1]} ${year}`;
  }
  return `${date.slice(5, 7)}/${date.slice(8, 10)}/${date.slice(0, 4)}`;
}

function drawGrid(max, width, height, left, top, plotWidth, plotHeight) {
  let content = '';
  for (let index = 0; index <= 4; index += 1) {
    const value = max * index / 4;
    const y = top + plotHeight - value / max * plotHeight;
    content += `<line x1="${left}" x2="${width - 16}" y1="${y}" y2="${y}" class="grid-line"/>`;
    content += text(left - 9, y + 3, fmt(value, 0), 'text-anchor="end"');
  }
  return content;
}

function chartMaximum(value) {
  const target = Math.max(0.01, value / 4);
  const magnitude = 10 ** Math.floor(Math.log10(target));
  const step = [1, 2, 2.5, 5, 10].map((multiple) => multiple * magnitude)
    .find((candidate) => candidate >= target) || target;
  return Math.ceil(value / step) * step;
}

function renderHistoryChart() {
  const frequency = $('frequency').value;
  const series = buildSelectedSeries();
  const visible = series.flatMap((item) => item.rows);
  const range = selectedRange();
  const step = frequency === 'daily' ? 86400000 : frequency === 'monthly' ? 30 * 86400000 : 365 * 86400000;
  const rangeStart = Date.parse(`${range.start.slice(0, 10)}T00:00:00Z`);
  const rangeEnd = Date.parse(`${range.end.slice(0, 10)}T00:00:00Z`);
  const stamps = visible.map((row) => row.stamp);
  const compareRange = $('compare-period-enabled').checked ? selectedRange('compare-') : null;
  const compareStamps = compareRange
    ? series.filter((item) => item.dash).flatMap((item) => item.rows.map((row) => row.stamp))
    : [];
  const minStamp = Math.min(...stamps, ...compareStamps, rangeStart);
  const maxStamp = Math.max(...stamps, ...compareStamps, rangeEnd);
  const width = 1000;
  const height = 300;
  const left = 64;
  const right = 18;
  const top = 14;
  const bottom = 39;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const maxValue = Math.max(1, ...visible.map((row) => row.value));
  const max = chartMaximum(maxValue);
  const x = (stamp) => maxStamp <= minStamp
    ? left + plotWidth / 2
    : left + (stamp - minStamp) / (maxStamp - minStamp) * plotWidth;
  const y = (value) => top + plotHeight - value / max * plotHeight;
  let content = drawGrid(max, width, height, left, top, plotWidth, plotHeight);

  if (!visible.length) {
    $('history-chart').innerHTML = '<p class="chart-note">No complete observations are available for this selection.</p>';
    $('history-legend').replaceChildren();
    $('history-note').textContent = 'Incomplete records are omitted; missing values are never treated as zero.';
    return;
  }

  const tickCount = Math.min(7, Math.max(2, Math.floor(plotWidth / 120)));
  for (let index = 0; index < tickCount; index += 1) {
    const stamp = minStamp + (maxStamp - minStamp) * index / Math.max(1, tickCount - 1);
    const date = new Date(stamp);
    const label = frequency === 'annual'
      ? String(date.getUTCFullYear())
      : frequency === 'monthly'
        ? `${MONTHS[date.getUTCMonth()]} ${String(date.getUTCFullYear()).slice(-2)}`
        : `${MONTHS[date.getUTCMonth()]} ${String(date.getUTCDate()).padStart(2, '0')}`;
    content += text(x(stamp), height - 12, label, 'text-anchor="middle"');
  }

  series.forEach((item) => {
    if (!item.rows.length) return;
    let path = '';
    let previousStamp = null;
    for (const row of item.rows) {
      const gap = previousStamp !== null && (row.stamp - previousStamp) > step * 1.5;
      path += `${!path || gap ? 'M' : 'L'}${x(row.stamp).toFixed(2)},${y(row.value).toFixed(2)} `;
      previousStamp = row.stamp;
    }
    content += `<path d="${path}" class="series-line" stroke="${item.color}" ${item.dash ? 'stroke-dasharray="6 5"' : ''}/>`;
  });

  content += `<line class="hover-line" x1="${left}" x2="${left}" y1="${top}" y2="${top + plotHeight}" visibility="hidden"/>`;
  content += `<rect class="chart-interaction" x="${left}" y="${top}" width="${plotWidth}" height="${plotHeight}" fill="transparent" tabindex="0" role="application" aria-label="Move across the ${frequency} precipitation chart to inspect values"/>`;
  $('history-chart').innerHTML = svg(
    content,
    `Precipitation history for ${current.name}; ${frequency} totals${series.length > 1 ? ' with state or period comparison' : ''}`,
    `0 0 ${width} ${height}`,
  );
  const chartSvg = $('history-chart').querySelector('svg');
  const interaction = chartSvg.querySelector('.chart-interaction');
  const hoverLine = chartSvg.querySelector('.hover-line');
  const tooltip = $('history-tooltip');
  const shell = document.querySelector('.chart-shell');
  const showNearest = (clientX) => {
    const rect = chartSvg.getBoundingClientRect();
    const svgX = (clientX - rect.left) / rect.width * width;
    const stamp = minStamp + Math.max(0, Math.min(1, (svgX - left) / plotWidth)) * (maxStamp - minStamp);
    hoverLine.setAttribute('x1', String(x(stamp)));
    hoverLine.setAttribute('x2', String(x(stamp)));
    hoverLine.setAttribute('visibility', 'visible');
    const nearest = series.map((item) => {
      let low = 0;
      let high = item.rows.length - 1;
      while (low < high) {
        const mid = Math.floor((low + high) / 2);
        if (item.rows[mid].stamp < stamp) low = mid + 1;
        else high = mid;
      }
      const candidate = item.rows[low];
      const previous = item.rows[low - 1];
      const row = candidate && previous && Math.abs(previous.stamp - stamp) < Math.abs(candidate.stamp - stamp)
        ? previous
        : candidate;
      return row && Math.abs(row.stamp - stamp) <= step * 0.55
        ? { item, row }
        : null;
    }).filter(Boolean);
    if (!nearest.length) {
      tooltip.hidden = true;
      return;
    }
    const dateText = dateLabel(nearest[0].row.date, frequency);
    tooltip.textContent = `${dateText}\n${nearest.map(({ item, row }) => `${item.label}: ${fmt(row.value)} mm`).join('\n')}`;
    const shellRect = shell.getBoundingClientRect();
    tooltip.style.left = `${Math.max(0, Math.min(clientX - shellRect.left, shellRect.width - 250))}px`;
    tooltip.style.top = `${Math.max(38, rect.top - shellRect.top + y(nearest[0].row.value) / height * rect.height)}px`;
    tooltip.hidden = false;
  };
  interaction.addEventListener('pointermove', (event) => showNearest(event.clientX));
  interaction.addEventListener('pointerleave', () => {
    hoverLine.setAttribute('visibility', 'hidden');
    tooltip.hidden = true;
  });
  interaction.addEventListener('focus', () => {
    const rect = chartSvg.getBoundingClientRect();
    showNearest(rect.left + rect.width * 0.5);
  });
  interaction.addEventListener('blur', () => {
    hoverLine.setAttribute('visibility', 'hidden');
    tooltip.hidden = true;
  });

  const legendStates = [...new Map(series.map((item) => [item.state.uf, item])).values()];
  $('history-legend').innerHTML = legendStates.map((item) =>
    `<span><i class="legend-key" style="background:${item.color}"></i>${esc(item.state.name)}</span>`,
  ).join('');
  $('history-note').textContent = `${frequency[0].toUpperCase()}${frequency.slice(1)} precipitation in millimeters · incomplete periods are omitted, never zero-filled.`;
}

function renderClimateChart() {
  const rows = current.climate.filter((row) => valid(row.mean_mm));
  if (!rows.length) {
    $('climate-chart').replaceChildren();
    return;
  }
  const width = 1000;
  const height = 260;
  const left = 56;
  const right = 16;
  const top = 16;
  const bottom = 34;
  const plotHeight = height - top - bottom;
  const maxValue = Math.max(1, ...rows.map((row) => Number(row.p90_mm) || 0));
  const max = chartMaximum(maxValue);
  const y = (value) => top + plotHeight - Number(value) / max * plotHeight;
  let content = drawGrid(max, width, height, left, top, width - left - right, plotHeight);
  rows.forEach((row, index) => {
    const x = left + (index + 0.5) * (width - left - right) / 12;
    const title = `${MONTH_NAMES[Number(row.month) - 1]} · mean ${fmt(Number(row.mean_mm))} mm · median ${fmt(Number(row.median_mm))} mm · P10 ${fmt(Number(row.p10_mm))} mm · P90 ${fmt(Number(row.p90_mm))} mm · ${row.n_years} years`;
    content += `<rect x="${x - 18}" y="${y(row.p90_mm)}" width="36" height="${Math.max(1, y(row.p10_mm) - y(row.p90_mm))}" fill="rgba(255,255,255,.15)"><title>${esc(title)}</title></rect>`;
    content += `<line x1="${x}" x2="${x}" y1="${y(row.p10_mm)}" y2="${y(row.p90_mm)}" stroke="rgba(255,255,255,.72)" stroke-width="2"/>`;
    content += `<rect x="${x - 11}" y="${y(row.mean_mm)}" width="22" height="${top + plotHeight - y(row.mean_mm)}" rx="2" fill="#FFFF00"><title>${esc(title)}</title></rect>`;
    content += `<line x1="${x - 8}" x2="${x + 8}" y1="${y(row.median_mm)}" y2="${y(row.median_mm)}" stroke="#FFFFFF" stroke-width="2"/>`;
    content += text(x, height - 10, MONTHS[Number(row.month) - 1], 'text-anchor="middle"');
  });
  $('climate-chart').innerHTML = svg(content, `Monthly precipitation climatology for ${current.name}`, `0 0 ${width} ${height}`);
}

function renderHeatmap() {
  const range = selectedRange();
  const firstYear = Number(range.start.slice(0, 4));
  const lastYear = Number(range.end.slice(0, 4));
  const rows = new Map(current.monthly.map((row) => [`${row.year}-${row.month}`, row]));
  const years = [];
  for (let year = lastYear; year >= firstYear; year -= 1) years.push(year);
  let html = `<thead><tr><th scope="col">Year</th>${MONTHS.map((month) => `<th scope="col">${month}</th>`).join('')}</tr></thead><tbody>`;
  years.forEach((year) => {
    html += `<tr><th scope="row">${year}</th>`;
    for (let month = 1; month <= 12; month += 1) {
      const row = rows.get(`${year}-${month}`);
      const complete = row?.complete && valid(row.precip_mm);
      const label = complete ? CATEGORY_LABELS[row.category] || 'Insufficient reference' : 'Missing data';
      const categoryClass = complete ? CATEGORY_CLASSES[row.category] || 'category-normal' : 'category-missing';
      html += `<td><button class="${categoryClass}" data-year="${year}" data-month="${month}" aria-label="${MONTHS[month - 1]} ${year}: ${label}, ${fmt(Number(row?.precip_mm))} mm" title="${MONTHS[month - 1]} ${year} · ${label} · ${fmt(Number(row?.precip_mm))} mm"></button></td>`;
    }
    html += '</tr>';
  });
  html += '</tbody>';
  $('heatmap').innerHTML = html;
  $('grid-period').textContent = `${firstYear}–${lastYear}`;
  $('cell-detail').textContent = 'Select a cell to inspect rainfall totals and historical thresholds.';
}

function showCell(year, month) {
  const row = current.monthly.find((item) => Number(item.year) === year && Number(item.month) === month);
  $('heatmap').querySelectorAll('.selected').forEach((button) => button.classList.remove('selected'));
  $('heatmap').querySelector(`[data-year="${year}"][data-month="${month}"]`)?.classList.add('selected');
  if (!row?.complete || !valid(row.precip_mm)) {
    $('cell-detail').textContent = `${MONTHS[month - 1]} ${year} · No complete total. Incomplete values are not treated as zero.`;
    return;
  }
  $('cell-detail').textContent = `${MONTHS[month - 1]} ${year} · ${fmt(Number(row.precip_mm))} mm · ${CATEGORY_LABELS[row.category] || 'Insufficient reference'}. P10 ${fmt(Number(row.p10_mm))} · P30 ${fmt(Number(row.p30_mm))} · P70 ${fmt(Number(row.p70_mm))} · P90 ${fmt(Number(row.p90_mm))} mm. Reference: ${row.n_ref_years ?? 0} years.${row.thresholds_degenerate ? ' Tied thresholds occur in this reference.' : ''}`;
}

function renderAnomalyChart() {
  const frequency = $('anomaly-frequency').value;
  const unit = $('anomaly-unit').value;
  const column = unit === 'zscore' ? 'zscore' : unit;
  const allRows = frequency === 'monthly'
    ? current.monthly.map((row) => ({ ...row, date: dateFromParts(row.year, row.month, 15) }))
    : current.annual.map((row) => ({ ...row, date: dateFromParts(row.year, 7, 1) }));
  const range = selectedRange();
  const startYear = Number(range.start.slice(0, 4));
  const endYear = Number(range.end.slice(0, 4));
  const startMonth = Number(range.start.slice(5, 7));
  const endMonth = Number(range.end.slice(5, 7));
  const rows = allRows.filter((row) => {
    if (Number(row.year) < startYear || Number(row.year) > endYear) return false;
    return frequency === 'annual'
      || (Number(row.year) !== startYear || Number(row.month) >= startMonth)
        && (Number(row.year) !== endYear || Number(row.month) <= endMonth);
  });
  const available = rows.filter((row) => valid(row[column]));
  if (!available.length) {
    $('anomaly-chart').replaceChildren();
    $('anomaly-subtitle').textContent = 'No anomaly values are available for this selection.';
    return;
  }
  const width = 1000;
  const height = 235;
  const left = 62;
  const right = 16;
  const top = 14;
  const zero = 120;
  const bottom = 26;
  const max = Math.max(1, ...available.map((row) => Math.abs(Number(row[column])))) * 1.08;
  const plotWidth = width - left - right;
  const plotHeight = zero - top;
  const y = (value) => zero - Number(value) / max * plotHeight;
  let content = '';
  for (let index = 0; index <= 4; index += 1) {
    const value = -max + max * index / 2;
    const yPosition = y(value);
    content += `<line x1="${left}" x2="${width - right}" y1="${yPosition}" y2="${yPosition}" class="grid-line"/>`;
    content += text(left - 8, yPosition + 3, fmt(value, 0), 'text-anchor="end"');
  }
  content += `<line x1="${left}" x2="${width - right}" y1="${zero}" y2="${zero}" class="zero-line"/>`;
  const slot = plotWidth / Math.max(rows.length, 1);
  rows.forEach((row, index) => {
    const value = Number(row[column]);
    const x = left + (index + 0.5) * slot;
    if (valid(value)) {
      const barY = Math.min(zero, y(value));
      const barHeight = Math.max(1, Math.abs(y(value) - zero));
      const label = `${row.date} · ${signed(value)} ${unit === 'zscore' ? 'Z' : unit === 'anomaly_pct' ? '%' : 'mm'}`;
      content += `<rect x="${x - Math.max(1, slot * 0.35)}" y="${barY}" width="${Math.max(1, slot * 0.7)}" height="${barHeight}" rx="1" fill="${value >= 0 ? SERIES_COLORS.primary : SERIES_COLORS.comparison}"><title>${esc(label)}</title></rect>`;
    }
    if (rows.length <= 24 || index % Math.ceil(rows.length / 12) === 0) {
      content += text(x, height - 8, frequency === 'monthly' ? `${MONTHS[Number(row.month) - 1]} ${String(row.year).slice(-2)}` : String(row.year), 'text-anchor="middle"');
    }
  });
  $('anomaly-chart').innerHTML = svg(content, `${frequency} precipitation anomalies for ${current.name}`, `0 0 ${width} ${height}`);
  $('anomaly-subtitle').textContent = `${frequency === 'monthly' ? 'Monthly departure from the same calendar-month mean' : 'Annual departure from the historical annual mean'} · ${range.startInput}–${range.endInput}`;
}

function trendReading(trend) {
  const slope = Number(trend.sens_slope_mm_yr);
  const significant = Boolean(trend.significant_fdr);
  const direction = !valid(slope) ? 'Unavailable' : slope > 0 ? 'Positive (estimated increase)' : slope < 0 ? 'Negative (estimated decrease)' : 'Zero';
  return { slope, significant, direction };
}

function renderTrend() {
  const trend = current.trend;
  const { slope, significant, direction } = trendReading(trend);
  const annualRows = current.annual.filter((row) => row.complete && valid(row.annual_total_mm));
  const range = selectedRange();
  const firstYear = Number(range.start.slice(0, 4));
  const lastYear = Number(range.end.slice(0, 4));
  const visibleRows = annualRows.filter((row) => Number(row.year) >= firstYear && Number(row.year) <= lastYear);

  $('slope').innerHTML = `${signed(slope, 2)} <em>mm/year</em>`;
  $('direction').textContent = direction;
  $('mk-p').textContent = pformat(Number(trend.p_value_mk));
  $('bh-p').textContent = pformat(Number(trend.p_adj_bh));
  $('trend-badge').textContent = trend.trend_class === 'dados_insuficientes'
    ? 'Insufficient data'
    : significant ? 'Significant trend' : 'Insufficient evidence';
  $('trend-period').textContent = `${trend.n_years} complete years · ${trend.first_year}–${trend.last_year} · fixed test on the full record`;
  $('trend-reading').textContent = `${direction}. ${significant ? `There is evidence of an ${slope > 0 ? 'increasing' : 'decreasing'} trend after BH adjustment (α = 0.05).` : 'There is insufficient statistical evidence to establish a trend after BH adjustment (α = 0.05).'} The slope is a historical estimate, not a forecast. The selected display period does not recalculate the fixed-reference test.`;

  const width = 1000;
  const height = 245;
  const left = 62;
  const right = 16;
  const top = 14;
  const bottom = 30;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const values = visibleRows.map((row) => Number(row.annual_total_mm));
  const residuals = annualRows.map((row) => Number(row.annual_total_mm) - slope * Number(row.year)).sort((first, second) => first - second);
  const middle = Math.floor(residuals.length / 2);
  const intercept = residuals.length
    ? residuals.length % 2
      ? residuals[middle]
      : (residuals[middle - 1] + residuals[middle]) / 2
    : 0;
  const estimateValues = [firstYear, lastYear].map((year) => slope * year + intercept);
  const max = Math.max(1, ...values, ...estimateValues.filter(Number.isFinite)) * 1.08;
  const min = Math.min(0, ...values, ...estimateValues.filter(Number.isFinite));
  const span = Math.max(1, max - min);
  const x = (year) => firstYear === lastYear
    ? left + plotWidth / 2
    : left + (year - firstYear) / (lastYear - firstYear) * plotWidth;
  const y = (value) => top + plotHeight - (value - min) / span * plotHeight;
  let content = '';
  for (let index = 0; index <= 4; index += 1) {
    const value = min + span * index / 4;
    const yPosition = y(value);
    content += `<line x1="${left}" x2="${width - right}" y1="${yPosition}" y2="${yPosition}" class="grid-line"/>`;
    content += text(left - 8, yPosition + 3, fmt(value, 0), 'text-anchor="end"');
  }
  const path = visibleRows.map((row, index) =>
    `${index === 0 || Number(row.year) !== Number(visibleRows[index - 1].year) + 1 ? 'M' : 'L'}${x(Number(row.year))},${y(Number(row.annual_total_mm))}`,
  ).join(' ');
  content += `<path d="${path}" class="series-line" stroke="${SERIES_COLORS.primary}"/>`;
  visibleRows.forEach((row) => {
    const year = Number(row.year);
    content += `<circle cx="${x(year)}" cy="${y(Number(row.annual_total_mm))}" r="3" fill="${SERIES_COLORS.primary}"><title>${year}: ${fmt(Number(row.annual_total_mm))} mm</title></circle>`;
    if ((year - firstYear) % Math.max(1, Math.ceil(visibleRows.length / 10)) === 0 || year === lastYear) {
      content += text(x(year), height - 8, year, 'text-anchor="middle"');
    }
  });
  if (valid(slope) && firstYear < lastYear) {
    content += `<line x1="${x(firstYear)}" x2="${x(lastYear)}" y1="${y(slope * firstYear + intercept)}" y2="${y(slope * lastYear + intercept)}" stroke="${SERIES_COLORS.comparison}" stroke-width="2" ${significant ? '' : 'stroke-dasharray="6 5"'}/>`;
  }
  $('trend-chart').innerHTML = svg(content, `Annual rainfall and Sen slope for ${current.name}`, `0 0 ${width} ${height}`);

  const noteText = String(trend.notes || 'No additional notes')
    .replace('autocorrelação significativa: p corrigido (Hamed-Rao)', 'Significant autocorrelation: Hamed–Rao corrected p-value')
    .replace('significativo só sem correção para múltiplos testes', 'Significant only without multiple-testing correction')
    .replace('série curta (<20 anos): baixo poder', 'Short series (<20 years): limited statistical power')
    .replace('anos faltantes na série (autocorrelação aproximada)', 'Missing years: approximate autocorrelation diagnostics');
  const details = [
    ['Pre-adjustment p-value', pformat(Number(trend.p_value_used))],
    ['P-value method', trend.p_value_method === 'hamed_rao' ? 'Hamed–Rao (variance correction constrained to ≥ 1)' : 'Original Mann–Kendall'],
    ['Autocorrelation detected', trend.autocorr_significant ? 'Yes' : 'No'],
    ['Holm-adjusted p-value', pformat(Number(trend.p_adj_holm))],
    ['Nominal 95% Sen confidence interval', `${signed(Number(trend.sens_ci_low_mm_yr))} to ${signed(Number(trend.sens_ci_high_mm_yr))} mm/year`],
    ['Confidence-interval note', 'Not adjusted for autocorrelation or multiple testing; does not replace the BH decision.'],
    ['Gaps between complete years', trend.has_gaps ? 'Yes; approximate autocorrelation diagnostics' : 'No'],
    ['Additional notes', noteText],
  ];
  $('trend-details').innerHTML = `<table class="stat-table">${details.map(([key, value]) => `<tr><td>${esc(key)}</td><td>${esc(value)}</td></tr>`).join('')}</table><p class="chart-note">BH controls the false discovery rate under its dependence assumptions. Holm provides a more conservative sensitivity analysis. Temporal correction does not establish source homogeneity.</p>`;
}

function renderModelEvaluation() {
  const model = data.machine_learning;
  const overall = model.overall;
  const rows = model.by_state;
  const wins = rows.filter((row) => row.winner_by_mae === 'Random Forest').length;
  $('rf-mae').textContent = `${fmt(Number(overall.random_forest_mae_mm))} mm`;
  $('baseline-mae').textContent = `${fmt(Number(overall.baseline_mae_mm))} mm`;
  $('mae-improvement').textContent = `${signed(Number(overall.mae_improvement_pct))}%`;
  $('model-wins').textContent = `Random Forest has lower MAE in ${wins} of 27 states`;

  const max = Math.max(1, ...rows.map((row) => Number(row.baseline_mae_mm)), ...rows.map((row) => Number(row.random_forest_mae_mm)));
  const stateRows = rows.slice().sort((a, b) => Number(b.random_forest_mae_mm) - Number(a.random_forest_mae_mm));
  $('model-state-chart').innerHTML = `<div class="model-state-scroll"><div class="model-state-grid">${stateRows.map((row) => `
    <div class="state-error-row" title="${esc(row.uf)} · seasonal naive ${fmt(Number(row.baseline_mae_mm))} mm · Random Forest ${fmt(Number(row.random_forest_mae_mm))} mm">
      <span>${esc(row.uf)}</span>
      <span class="error-bars" aria-hidden="true">
        <i class="error-bar baseline" style="width:${Math.max(1, Number(row.baseline_mae_mm) / max * 100)}%"></i>
        <i class="error-bar model" style="width:${Math.max(1, Number(row.random_forest_mae_mm) / max * 100)}%"></i>
      </span>
      <strong>${fmt(Number(row.random_forest_mae_mm))}</strong>
    </div>`).join('')}</div></div>`;

  const horizon = model.recursive_by_horizon;
  const width = 1000;
  const height = 230;
  const left = 62;
  const right = 18;
  const top = 13;
  const bottom = 31;
  const plotHeight = height - top - bottom;
  const plotWidth = width - left - right;
  const maxMae = Math.max(
    1,
    ...horizon.map((row) => Number(row.baseline_mae_mm)),
    ...horizon.map((row) => Number(row.random_forest_mae_mm)),
  );
  const y = (value) => top + plotHeight - Number(value) / maxMae * plotHeight;
  let content = drawGrid(maxMae, width, height, left, top, plotWidth, plotHeight);
  const groupWidth = plotWidth / Math.max(horizon.length, 1);
  horizon.forEach((row, index) => {
    const center = left + (index + 0.5) * groupWidth;
    const baseline = Number(row.baseline_mae_mm);
    const forest = Number(row.random_forest_mae_mm);
    content += `<rect x="${center - 17}" y="${y(baseline)}" width="13" height="${top + plotHeight - y(baseline)}" rx="2" fill="${SERIES_COLORS.comparison}"><title>Horizon ${row.horizon} · seasonal naive ${fmt(baseline)} mm MAE</title></rect>`;
    content += `<rect x="${center + 4}" y="${y(forest)}" width="13" height="${top + plotHeight - y(forest)}" rx="2" fill="${SERIES_COLORS.primary}"><title>Horizon ${row.horizon} · Random Forest ${fmt(forest)} mm MAE</title></rect>`;
    content += text(center, height - 9, `Month ${row.horizon}`, 'text-anchor="middle"');
  });
  $('recursive-chart').innerHTML = svg(content, 'Recursive backtest mean absolute error by forecast horizon', `0 0 ${width} ${height}`);
  $('recursive-note').textContent = `Aggregated recursive test set · ${fmt(Number(horizon[0]?.samples), 0)} samples per horizon. Scores vary by state; they are not guarantees of future accuracy.`;

}

function tableRows() {
  const frequency = $('frequency').value;
  const range = selectedRange();
  if (frequency === 'daily') {
    return getSeriesRows(current, frequency, range).slice(0, 100).map((row) => ({
      date: row.date,
      value: row.value,
      anomaly: '',
      anomalyPct: '',
      zscore: '',
      validDays: '1 / 1',
    }));
  }
  if (frequency === 'annual') {
    return current.annual.filter((row) => row.complete && valid(row.annual_total_mm)
      && row.year >= Number(range.start.slice(0, 4))
      && row.year <= Number(range.end.slice(0, 4)))
      .map((row) => ({
        date: String(row.year),
        value: Number(row.annual_total_mm),
        anomaly: row.anomaly_mm,
        anomalyPct: row.anomaly_pct,
        zscore: row.zscore,
        validDays: `${row.n_valid_days} days`,
      }));
  }
  return current.monthly.filter((row) => row.complete && valid(row.precip_mm)
    && dateFromParts(row.year, row.month, 15) >= range.start
    && dateFromParts(row.year, row.month, 15) <= range.end)
    .map((row) => ({
      date: `${MONTHS[Number(row.month) - 1]} ${row.year}`,
      value: Number(row.precip_mm),
      anomaly: row.anomaly_mm,
      anomalyPct: row.anomaly_pct,
      zscore: row.zscore,
      validDays: `${row.n_valid_days} / ${row.n_days_expected}`,
    }));
}

function renderTable() {
  const rows = tableRows();
  const frequency = $('frequency').value;
  const headers = frequency === 'daily'
    ? ['Date', 'Rainfall (mm)', 'Valid days']
    : ['Period', 'Rainfall (mm)', 'Anomaly (mm)', 'Anomaly (%)', 'Z-score', 'Coverage'];
  const visibleRows = rows.slice(0, 100);
  $('data-table').innerHTML = `<thead><tr>${headers.map((header) => `<th scope="col">${header}</th>`).join('')}</tr></thead><tbody>${visibleRows.map((row) => frequency === 'daily'
    ? `<tr><td>${esc(row.date)}</td><td>${fmt(row.value)}</td><td>${row.validDays}</td></tr>`
    : `<tr><td>${esc(row.date)}</td><td>${fmt(row.value)}</td><td>${signed(Number(row.anomaly))}</td><td>${signed(Number(row.anomalyPct))}</td><td>${fmt(Number(row.zscore), 2)}</td><td>${row.validDays}</td></tr>`,
  ).join('')}</tbody>`;
  const range = selectedRange();
  $('table-period').textContent = `${rows.length} ${frequency} records · ${range.startInput}–${range.endInput}${rows.length > 100 ? ' · first 100 shown; export includes all selected records' : ''}`;
}

function renderQuality() {
  const quality = current.quality;
  const first = Date.parse(`${quality.first_date}T00:00:00Z`);
  const last = Date.parse(`${quality.last_date}T00:00:00Z`);
  const expectedDays = Math.floor((last - first) / 86400000) + 1;
  const received = Number(quality.n_days_received);
  const coverage = expectedDays > 0 ? received / expectedDays * 100 : null;
  $('point-detail').textContent = `Coordinates: ${fmt(current.latitude, 5)}°, ${fmt(current.longitude, 5)}°.`;
  $('coverage-detail').textContent = `The fixed 2005–2025 statistical reference is not a standard 30-year climate normal. Filtered chart periods are separate from the reference used for percentiles and trend inference.`;
  $('quality-detail').textContent = `${fmt(coverage, 1)}% daily coverage within the recorded date span · ${fmt(received, 0)} daily records · ${fmt(Number(quality.n_internal_missing_dates), 0)} internal missing dates · longest gap: ${fmt(Number(quality.longest_gap_days), 0)} days.`;
}

function renderContext() {
  $('dataset-period').textContent = `${data.reference.start_year}–${data.reference.end_year} · ${data.states.length} reference points`;
}

function render() {
  normalizeRanges();
  current = data.states.find((state) => state.uf === $('state').value);
  if (!current) throw new Error('The selected federal unit is missing from the analysis data.');
  if ($('compare-state-enabled').checked && $('compare-state').value === current.uf) {
    $('compare-state').value = data.states.find((state) => state.uf !== current.uf).uf;
  }
  renderContext();
  renderIndicators();
  renderHistoryChart();
  renderClimateChart();
  renderHeatmap();
  renderAnomalyChart();
  renderTrend();
  renderTable();
  renderQuality();
  renderModelEvaluation();
  updateURL();
}

function updateURL() {
  const range = selectedRange();
  const params = new URLSearchParams(location.search);
  params.set('uf', current.uf);
  params.set('resolucao', $('frequency').value);
  params.set('inicio', range.startInput);
  params.set('fim', range.endInput);
  if ($('compare-state-enabled').checked) params.set('uf_comparacao', $('compare-state').value);
  else params.delete('uf_comparacao');
  if ($('compare-period-enabled').checked) {
    const comparison = selectedRange('compare-');
    params.set('comparacao_inicio', comparison.startInput);
    params.set('comparacao_fim', comparison.endInput);
  } else {
    params.delete('comparacao_inicio');
    params.delete('comparacao_fim');
  }
  history.replaceState(null, '', `?${params}${location.hash}`);
}

function exportCsv() {
  const frequency = $('frequency').value;
  const series = buildSelectedSeries();
  const header = ['federal_unit', 'state', 'resolution', 'period', 'precipitation_mm', 'category', 'anomaly_mm', 'anomaly_pct', 'z_score', 'comparison'];
  const rows = [];
  for (const item of series) {
    for (const row of item.rows) {
      rows.push([
        item.state.uf,
        item.state.name,
        frequency,
        row.date,
        row.value,
        row.category ?? '',
        row.anomaly_mm ?? '',
        row.anomaly_pct ?? '',
        row.zscore ?? '',
        item.dash ? 'comparison period' : $('compare-state-enabled').checked && item.state.uf === $('compare-state').value ? 'comparison state' : 'selected',
      ]);
    }
  }
  const csv = [header, ...rows].map((row) =>
    row.map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`).join(','),
  ).join('\r\n');
  const url = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `for_ecast_${current.uf.toLowerCase()}_${frequency}_${selectedRange().startInput}_${selectedRange().endInput}.csv`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function bindControls() {
  for (const id of ['state', 'compare-state', 'reference-year', 'period-start', 'period-end', 'compare-period-start', 'compare-period-end']) {
    $(id).addEventListener('change', () => {
      try {
        render();
      } catch (error) {
        showError(error);
      }
    });
  }
  $('compare-state-enabled').addEventListener('change', () => {
    $('compare-state-group').hidden = !$('compare-state-enabled').checked;
    render();
  });
  $('compare-period-enabled').addEventListener('change', () => {
    $('compare-period-group').hidden = !$('compare-period-enabled').checked;
    render();
  });
  $('frequency').addEventListener('change', async () => {
    try {
      configurePeriodInputs($('frequency').value);
      if ($('frequency').value === 'daily') await loadDailyData();
      render();
    } catch (error) {
      showError(error);
    }
  });
  $('anomaly-frequency').addEventListener('change', renderAnomalyChart);
  $('anomaly-unit').addEventListener('change', renderAnomalyChart);
  $('download').addEventListener('click', exportCsv);
  $('reset-filters').addEventListener('click', async () => {
    $('state').value = 'AC';
    $('compare-state').value = 'SP';
    $('reference-year').value = $('reference-year').options[$('reference-year').options.length - 1].value;
    $('compare-state-enabled').checked = false;
    $('compare-state-group').hidden = true;
    $('compare-period-enabled').checked = false;
    $('compare-period-group').hidden = true;
    $('frequency').value = 'annual';
    configurePeriodInputs('annual');
    if ($('frequency').value === 'daily') await loadDailyData();
    render();
  });
  $('heatmap').addEventListener('click', (event) => {
    const cell = event.target.closest('button[data-year]');
    if (cell) showCell(Number(cell.dataset.year), Number(cell.dataset.month));
  });
}

async function loadDailyData() {
  if (dailyByState) return;
  $('sidebar-status').textContent = 'Loading daily observations…';
  const response = await fetch('../data/precipitation/processed/precipitacao_diaria_27_pontos_2005_2025.csv');
  if (!response.ok) throw new Error(`Could not load the daily precipitation file (HTTP ${response.status}).`);
  const csv = await response.text();
  const lines = csv.split(/\r?\n/);
  const columns = lines[0].replace(/^\uFEFF/, '').split(',');
  const stateIndex = columns.indexOf('uf');
  const dateIndex = columns.indexOf('data_inicio');
  const valueIndex = columns.indexOf('precipitacao_mm');
  const completeIndex = columns.indexOf('completo');
  if ([stateIndex, dateIndex, valueIndex, completeIndex].some((index) => index < 0)) {
    throw new Error('The daily precipitation file is missing required columns.');
  }
  const grouped = new Map();
  const climatologySums = new Map();
  const climatologyCounts = new Map();
  for (let index = 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line) continue;
    const fields = line.split(',');
    const state = fields[stateIndex];
    const rawValue = fields[valueIndex];
    if (fields[completeIndex] !== 'True' || !rawValue) continue;
    const value = Number(rawValue);
    if (!Number.isFinite(value)) continue;
    const date = fields[dateIndex];
    const dateCode = Number(date.replaceAll('-', ''));
    if (!grouped.has(state)) grouped.set(state, []);
    grouped.get(state).push([dateCode, value]);
    const monthDay = date.slice(5);
    const key = `${state}:${monthDay}`;
    climatologySums.set(key, (climatologySums.get(key) || 0) + value);
    climatologyCounts.set(key, (climatologyCounts.get(key) || 0) + 1);
  }
  dailyByState = new Map();
  for (const [state, records] of grouped) {
    const dates = new Uint32Array(records.length);
    const values = new Float64Array(records.length);
    records.forEach(([date, value], index) => {
      dates[index] = date;
      values[index] = value;
    });
    dailyByState.set(state, { dates, values });
  }
  dailyClimatology = new Map();
  for (const state of dailyByState.keys()) {
    const values = new Map();
    for (let month = 1; month <= 12; month += 1) {
      const days = new Date(Date.UTC(2020, month, 0)).getUTCDate();
      for (let day = 1; day <= days; day += 1) {
        const monthDay = `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const key = `${state}:${monthDay}`;
        const count = climatologyCounts.get(key) || 0;
        if (count) values.set(monthDay, climatologySums.get(key) / count);
      }
    }
    dailyClimatology.set(state, values);
  }
  $('sidebar-status').textContent = 'Daily observations loaded · 27 reference points';
}

function showError(error) {
  $('load-error').textContent = error instanceof Error ? error.message : 'An unexpected error occurred.';
  $('load-error').hidden = false;
  $('sidebar-status').textContent = 'Dashboard data unavailable';
}

async function initialize() {
  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error(`Could not load dashboard analysis data (HTTP ${response.status}).`);
    data = await response.json();
    if (!Array.isArray(data.states) || data.states.length !== 27) {
      throw new Error('Expected historical analysis data for all 27 federal units.');
    }
    const states = data.states.slice().sort((first, second) => first.name.localeCompare(second.name, 'en'));
    makeSelect($('state'), states, 'AC');
    makeSelect($('compare-state'), states, 'SP');
    const params = new URLSearchParams(location.search);
    const validState = (value) => states.some((state) => state.uf === value);
    $('state').value = validState(params.get('uf')) ? params.get('uf') : 'AC';
    $('compare-state').value = validState(params.get('uf_comparacao')) ? params.get('uf_comparacao') : 'SP';
    const annualYears = [...new Set(data.states.flatMap((state) => state.annual
      .filter((row) => row.complete && valid(row.annual_total_mm))
      .map((row) => Number(row.year))))].sort((first, second) => first - second);
    $('reference-year').replaceChildren(...annualYears.map((year) => {
      const option = document.createElement('option');
      option.value = String(year);
      option.textContent = String(year);
      return option;
    }));
    $('reference-year').value = String(annualYears.at(-1));
    if (['annual', 'monthly', 'daily'].includes(params.get('resolucao'))) {
      $('frequency').value = params.get('resolucao');
    }
    configurePeriodInputs($('frequency').value);
    const frequency = $('frequency').value;
    for (const [id, key] of [
      ['period-start', 'inicio'],
      ['period-end', 'fim'],
      ['compare-period-start', 'comparacao_inicio'],
      ['compare-period-end', 'comparacao_fim'],
    ]) {
      const value = params.get(key);
      if (value) $(id).value = value;
    }
    $('compare-state-enabled').checked = validState(params.get('uf_comparacao'));
    $('compare-state-group').hidden = !$('compare-state-enabled').checked;
    $('compare-period-enabled').checked = Boolean(params.get('comparacao_inicio') || params.get('comparacao_fim'));
    $('compare-period-group').hidden = !$('compare-period-enabled').checked;

    for (const id of ['state', 'compare-state', 'reference-year', 'frequency', 'period-start', 'period-end', 'compare-period-start', 'compare-period-end', 'compare-state-enabled', 'compare-period-enabled', 'download', 'reset-filters']) {
      $(id).disabled = false;
    }
    $('reference-period').textContent = `${data.reference.start_year}–${data.reference.end_year}`;
    $('sidebar-status').textContent = 'Monthly and annual analysis data loaded';
    $('content').hidden = false;
    bindControls();
    if (frequency === 'daily') await loadDailyData();
    render();
    const section = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (section) requestAnimationFrame(() => section.scrollIntoView());
  } catch (error) {
    showError(error);
  }
}

initialize();
