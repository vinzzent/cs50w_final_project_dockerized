
import {
    colorPalette, datetimeFormats, createLineChart, createBarChart, extractMappedAttributes, aggregateByAttributes, sortDataByDateField,
    sortDataByNumberField, createDataset, pickColor, groupDataByLabel, filterData
} from './chartUtils.js';

const sourceData = JSON.parse(document.getElementById('chart-data').textContent);

let datetimeCharts = {};
let charChart;

//////////////////////////////

/**
 * Updates the time-related options of a chart based on the specified datetime level.
 * @param {Object} chart - The chart object to update.
 * @param {string} datetimeLevel - The level of datetime granularity (e.g., 'day', 'month') to set for the chart.
 */

function updateDateTimeChartOptions(chart, datetimeLevel) {
    chart.options.scales.x.time.unit = datetimeLevel;
    chart.options.scales.x.time.tooltipFormat = datetimeFormats[datetimeLevel];
    chart.options.scales.x.time.displayFormats = datetimeFormats;
}

//////////////////////////////

/**
 * Updates the datetime chart based on user selections for time unit, legend, and date range.
 * @param {string} fieldname - The identifier used to locate relevant UI elements and update the chart.
 */

function updateDateTimeChart(fieldname) {
    const timeunitSelector = document.getElementById(`${fieldname}-time-unit-selector`);
    if (!timeunitSelector) {
        console.error(`Time unit selector for ${fieldname} not found.`);
        return;
    }

    const legendSelector = document.getElementById(`${fieldname}-legend-selector`);
    if (!legendSelector) {
        console.error(`Legend selector for ${fieldname} not found.`);
        return;
    }

    const startDateInput = document.getElementById(`${fieldname}-start-date-input`);
    if (!startDateInput) {
        console.error(`Start date input for ${fieldname} not found.`);
        return;
    }

    const endDateInput = document.getElementById(`${fieldname}-end-date-input`);
    if (!endDateInput) {
        console.error(`End date input for ${fieldname} not found.`);
        return;
    }

    const datetimeChart = datetimeCharts[fieldname];

    const mappedAttributes = datetimeChart?.mappedAttributes;
    if (!mappedAttributes) {
        console.error(`Mapped fields for ${fieldname} not found.`);
        return;
    }

    const datetimeLevel = timeunitSelector.value;    
    const groupKeys = [];
    const legendStrValue = legendSelector.value;

    if (legendStrValue === "") {
        delete mappedAttributes.legend;
    } else {
        const legendValue = Number(legendStrValue);
        mappedAttributes.legend = legendValue;
        groupKeys.push('legend');
    }

    let startDate = dateFns.parseISO(startDateInput.value);
    startDate = startDate.toString() === 'Invalid Date' ? "" : startDate;

    let endDate = dateFns.parseISO(endDateInput.value);
    endDate = endDate.toString() === 'Invalid Date' ? "" : dateFns.endOfDay(endDate);

    const data = sourceData?.dataset;
    if (!data) {
        console.error('Source data is undefined or invalid.');
        return null;
    }
    const reducedData = extractMappedAttributes(data, mappedAttributes);
    const filteredData = (startDate || endDate) ? filterData(reducedData, undefined, { 'x': { 'start': startDate, 'end': endDate } }) : reducedData;
    const aggregatedData = aggregateByAttributes(filteredData, 'y', groupKeys, { 'x': datetimeLevel });
    const sortedData = sortDataByDateField(aggregatedData, 'x');
    const colors = colorPalette.slice();
    const datasets = [];

    const groupedData = legendStrValue
        ? Object.entries(groupDataByLabel(sortedData, 'x', 'y', 'legend'))
        : [[null, sortedData]];  // Use null as a placeholder if no legend value

    datasets.push(...groupedData.map(data =>
        createDataset(data[1], data[0] || 'Activity Events', pickColor(colors, false))
    ));

    const chartData = { datasets: datasets };

    updateDateTimeChartOptions(datetimeChart, datetimeLevel); // Update chart options
    datetimeChart.data = chartData;
    datetimeChart.mappedAttributes = mappedAttributes;
    datetimeChart.update();
}

//////////////////////////////

/**
 * Updates the character chart based on selected field, date range, and sort direction. 
 * This function retrieves the user's input from the UI elements (field selector, start date, end date, 
 * and sort direction) and uses these values to filter, aggregate, sort, and update the chart data.
 */
function updateCharChart() {
    // Retrieve and validate UI elements
    const fieldSelector = document.getElementById('charfield-selector');
    if (!fieldSelector) {
        console.error('Field selector not found.');
        return;
    }

    const sortDirectionSelector = document.getElementById('sort-direction-selector');
    if (!sortDirectionSelector) {
        console.error('Sort direction selector not found.');
        return;
    }

    const startDateInput = document.getElementById('first-datetime-start-date-input') || {};
    if (!(startDateInput instanceof HTMLElement)) {
        startDateInput.value = "";
    }

    const endDateInput = document.getElementById('first-datetime-end-date-input') || {};
    if (!(endDateInput instanceof HTMLElement)) {
        endDateInput.value = "";
    }

    // Retrieve the chart and its mapped attributes
    const chart = charChart;
    const mappedAttributes = chart?.mappedAttributes;
    if (!mappedAttributes) {
        console.error('Mapped fields for chart not found.');
        return;
    }

    // Update mapped attributes based on selected field
    mappedAttributes.label = fieldSelector.value;
   
    // Parse and validate date inputs
    let startDate = dateFns.parseISO(startDateInput.value);
    startDate = startDate.toString() == 'Invalid Date' ? "" : startDate;  

    let endDate = dateFns.parseISO(endDateInput.value);
    endDate = endDate.toString() === 'Invalid Date' ? "" : dateFns.endOfDay(endDate);

    // Update date field in mapped attributes if dates are valid
    if (startDate || endDate) {
        mappedAttributes.date = sourceData.fieldtypes.indexOf('DateTimeField');
    } else {
        delete mappedAttributes.date;
    }

    // Extract, filter, aggregate, and sort data
    const data = sourceData.dataset;
    const reducedData = extractMappedAttributes(data, mappedAttributes);
    const filteredData = (startDate || endDate) 
        ? filterData(reducedData, undefined, { date: { start: startDate, end: endDate } }) 
        : reducedData;
    const aggregatedData = aggregateByAttributes(filteredData, 'value', ['label']);
    const sortDirection = sortDirectionSelector.value;
    const sortedData = sortDirection 
        ? sortDataByNumberField(aggregatedData, 'value', sortDirection) 
        : aggregatedData;

    // Prepare labels and values for the chart
    const labels = sortedData.map(item => item.label);
    const values = sortedData.map(item => item.value);
    
    // Generate new dataset and update the chart
    const color = pickColor(colorPalette.slice(), true);
    const displayname = sourceData.displaynames[mappedAttributes['label']];
    const dataset = createDataset(values, 'Activity Events by ' + displayname, color);
    chart.data = { labels, datasets: [dataset] };
    chart.mappedAttributes = mappedAttributes;
    chart.update();
}

//////////////////////////////

/**
 * Initializes a datetime chart with default settings and data.
 * @param {string} fieldname - The identifier for the chart.
 * @param {Object} mappedAttributes - Attributes used for mapping data.
 * @param {string} datetimeLevel - The level of datetime granularity for the chart.
 * @returns {Object|null} The initialized chart object or null if initialization fails.
 */
function initializeDateTimeChart(fieldname, mappedAttributes, datetimeLevel) {
    // Retrieve and validate canvas element
    const canvasElement = document.getElementById(fieldname + '-canvas');
    if (!canvasElement) {
        console.error(`Canvas element for ${fieldname} not found.`);
        return null;
    }

    const ctx = canvasElement.getContext('2d');
    const data = sourceData?.dataset;
    if (!data) {
        console.error('Source data is undefined or invalid.');
        return null;
    }

    // Process data and create chart
    const reducedData = extractMappedAttributes(data, mappedAttributes);
    const aggregatedData = aggregateByAttributes(reducedData, 'y', [], { 'x': datetimeLevel });
    const sortedData = sortDataByDateField(aggregatedData, 'x');    
    const color = pickColor(colorPalette.slice(), false);        
    const dataset = createDataset(sortedData, 'Activity Events', color);
    const chartData = { datasets: [dataset] };

    // Create the chart
    const datetimeChart = createLineChart(ctx, chartData, datetimeLevel, datetimeFormats, datetimeFormats[datetimeLevel]);

    // Explicitly set the mappedAttributes
    datetimeChart.mappedAttributes = mappedAttributes;

    return datetimeChart;
}

//////////////////////////////

/**
 * Initializes a char chart with mapped attributes and default settings.
 * 
 * @param {Object} mappedAttributes - Attributes used to map and extract data.
 * @returns {Object|null} The initialized chart object or null if initialization fails.
 */
function initializeCharChart(mappedAttributes) {
    // Retrieve and validate the canvas element
    const canvasElement = document.getElementById('charfield-canvas');
    if (!canvasElement) {
        console.error('Canvas element with ID charfield-canvas not found.');
        return null;
    }

    // Get the canvas context
    const ctx = canvasElement.getContext('2d');

    // Retrieve and validate source data
    const data = sourceData?.dataset;
    if (!data) {
        console.error('Source data is undefined or invalid.');
        return null;
    }

    // Process data: extract, aggregate, and prepare labels and values
    const reducedData = extractMappedAttributes(data, mappedAttributes);
    const aggregatedData = aggregateByAttributes(reducedData, 'value', ['label']);
    const labels = aggregatedData.map(item => item.label);
    const values = aggregatedData.map(item => item.value);

    // Generate chart dataset
    const color = pickColor(colorPalette.slice(), true);
    const displayname = sourceData.displaynames[mappedAttributes['label']];
    const dataset = createDataset(values, 'Activity Events by ' + displayname, color);

    // Define chart data structure
    const chartData = { labels, datasets: [dataset] };

    // Create and return the bar chart
    const cChart = createBarChart(ctx, chartData);
    cChart.mappedAttributes = mappedAttributes;

    return cChart;
}

//////////////////////////////

/**
 * Initializes charts by setting up event listeners and creating chart instances.
 */
function initializeCharts() {
    const { fieldtypes, fields } = sourceData;

    fields.forEach((field, n) => {
        if (fieldtypes[n] === 'DateTimeField') {
            const mappedAttributes = { 'x': n, 'y': fields.length - 1 };
            const datetimeChart = initializeDateTimeChart(field, mappedAttributes, 'day');
            datetimeCharts[field] = datetimeChart;

            // Setup event listeners for all relevant inputs
            ['time-unit-selector', 'legend-selector', 'start-date-input', 'end-date-input'].forEach(type => {
                const element = document.getElementById(`${field}-${type}`);
                if (element) {
                    element.addEventListener('change', () => updateDateTimeChart(field));
                } else {
                    console.error(`${type.replace(/-/g, ' ')} for ${field} not found.`);
                }
            });
        }
    });
    if (fieldtypes.includes('CharField')) {
        const ids = ['charfield-selector', 'sort-direction-selector'];

        ids.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', updateCharChart);
            } else {
                console.error(`Element with ID "${id}" not found.`);
            }
        });
        if (fieldtypes.includes('DateTimeField')) {
            const ids = ['first-datetime-start-date-input', 'first-datetime-end-date-input'];
            ids.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', updateCharChart);
                } else {
                    console.error(`Element with ID "${id}" not found.`);
                }
            });
        }

        const index = fieldtypes.indexOf('CharField');
        const mappedAttributes = {label: index, value: fields.length - 1 };
        charChart = initializeCharChart(mappedAttributes);
    }
}

// Wait for the DOM to load before running the initialize function
document.addEventListener('DOMContentLoaded', initializeCharts);