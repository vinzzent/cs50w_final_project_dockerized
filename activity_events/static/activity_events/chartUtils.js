//////////////////////////////
// Exportable variables
//////////////////////////////

export const colorPalette = [  
  { dodgerBlue: 'rgba(30, 144, 255, 1)' },
  { deepPink: 'rgba(255, 20, 147, 1)' },
  { chartreuse: 'rgba(127, 255, 0, 1)' },
  { cyan: 'rgba(0, 255, 255, 1)' },
  { magenta: 'rgba(255, 0, 255, 1)' },
  { blue: 'rgba(0, 0, 255, 1)' },
  { purple: 'rgba(128, 0, 128, 1)' },
  { indigo: 'rgba(75, 0, 130, 1)' },
  { violet: 'rgba(238, 130, 238, 1)' },
  { orange: 'rgba(255, 159, 64, 1)' },
  { gold: 'rgba(255, 215, 0, 1)' },
  { lime: 'rgba(0, 255, 0, 1)' },
  { springGreen: 'rgba(0, 255, 127, 1)' },
  { peachPuff: 'rgba(255, 218, 185, 1)' },
  { wheat: 'rgba(245, 222, 179, 1)' },
  { lightYellow: 'rgba(255, 206, 86, 1)' },
  { lightCyan: 'rgba(75, 192, 192, 1)' },
  { skyBlue: 'rgba(135, 206, 235, 1)' },
  { lightBlue: 'rgba(173, 216, 230, 1)' },
  { lightSalmon: 'rgba(255, 160, 122, 1)' },
  { salmon: 'rgba(250, 128, 114, 1)' },
  { coral: 'rgba(255, 127, 80, 1)' },  
  { paleGreen: 'rgba(152, 251, 152, 1)' },
  { midnightBlue: 'rgba(25, 25, 112, 1)' },
  { saddleBrown: 'rgba(139, 69, 19, 1)' },
  { fireBrick: 'rgba(178, 34, 34, 1)' },
  { sienna: 'rgba(160, 82, 45, 1)' },
  { darkSlateGray: 'rgba(47, 79, 79, 1)' },
  { maroon: 'rgba(128, 0, 0, 1)' },
  { navy: 'rgba(0, 0, 128, 1)' },
  { forestGreen: 'rgba(34, 139, 34, 1)' },
  { lightCoral: 'rgba(255, 99, 132, 1)' }
];

//////////////////////////////

export const datetimeFormats = {
  hour: 'yyyy MMM d HH:00',
  day: 'yyyy MMM d',
  month: 'yyyy MMM',
  year: 'yyyy'
}


//////////////////////////////
// Internal variables
//////////////////////////////

const DOUBLE_CLICK_TIMEOUT = 300; // Timeout in milliseconds
let clickCounter = 0;
let clickTimeout;


//////////////////////////////
// Internal functions
//////////////////////////////

function generateRandomRGBA() {
  const r = Math.floor(Math.random() * 256); // Random value between 0-255 for red
  const g = Math.floor(Math.random() * 256); // Random value between 0-255 for green
  const b = Math.floor(Math.random() * 256); // Random value between 0-255 for blue
  const a = 1;
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

//////////////////////////////

function adjustRGBAAlpha(rgbaColor, newAlpha) {
  // Ensure newAlpha is between 0 and 1
  newAlpha = Math.max(0, Math.min(1, newAlpha));

  // Match the RGBA components using a regex
  const rgbaMatch = rgbaColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);

  if (!rgbaMatch) {
    throw new Error('Invalid RGBA color format');
  }
  
  // Extract the red, green, and blue values
  const r = rgbaMatch[1];
  const g = rgbaMatch[2];
  const b = rgbaMatch[3];

  // Return the new RGBA string with the updated alpha
  return `rgba(${r}, ${g}, ${b}, ${newAlpha})`;
}

//////////////////////////////

function getStartOfPeriod(parsedDate, level) {
  const utcDate = dateFns.parseISO(parsedDate);
  const startDate = (() => {
    switch (level) {
      case 'year':
        return dateFns.startOfYear(utcDate);
      case 'month':
        return dateFns.startOfMonth(utcDate);
      case 'day':
        return dateFns.startOfDay(utcDate);
      case 'hour':
        return dateFns.startOfHour(utcDate);
      default:
        return dateFns.startOfDay(utcDate); // Default to start of the day if level is unknown
    }
  })();

  return startDate;
}

//////////////////////////////
// Exportable functions
//////////////////////////////

/**
 * Creates a responsive line chart using Chart.js.
 * @param {CanvasRenderingContext2D} ctx - The context of the canvas element.
 * @param {Object} chartData - The data object for the chart, including datasets.
 * @param {string} unit - The time unit for the x-axis (e.g., 'day', 'month', 'year').
 * @param {Object} displayFormats - Format for displaying time on the x-axis.
 * @param {string} tooltipFormat - Format for the tooltip displaying time.
 * @returns {Chart} - The created Chart instance with interactive dataset visibility.
 */

export function createLineChart(ctx, chartData, unit, displayFormats, tooltipFormat) {
  return new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
      responsive: true,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: unit,
            tooltipFormat: tooltipFormat,
            displayFormats: displayFormats            
          },          
          grid: {
            display: false,
          }
        },
        y: {
          grid: {
            display: false,
          }          
        }
      },
      plugins: {
        legend: {
          onClick: (e, legendItem, legend) => {
            const index = legendItem.datasetIndex;
            const chart = legend.chart;

            clickCounter++;

            if (clickCounter === 1) {
              // Start the timeout for detecting double-click
              clickTimeout = setTimeout(() => {
                if (clickCounter === 1) {
                  // Single-click action
                  chart.data.datasets.forEach((dataset, i) => {
                    if (i === index) {
                      dataset.hidden = !dataset.hidden; // Toggle the visibility of the selected dataset
                    }
                  });
                }
                // Reset clickCounter
                clickCounter = 0;
                chart.update();
              }, DOUBLE_CLICK_TIMEOUT);
            } else if (clickCounter > 1) {
              // Double-click detected
              clearTimeout(clickTimeout);

              // Check if all datasets are visible
              const allVisible = chart.data.datasets.every(dataset => !dataset.hidden);

              if (allVisible) {
                // If all datasets are visible, show only the selected dataset
                chart.data.datasets.forEach((dataset, i) => {
                  dataset.hidden = i !== index;
                });
              } else {
                // If not all datasets are visible, show all datasets
                chart.data.datasets.forEach(dataset => {
                  dataset.hidden = false;
                });
              }

              // Reset clickCounter
              clickCounter = 0;
              chart.update();
            }
          }
        }

      }
    }
  });
}

//////////////////////////////

export function createBarChart(ctx, data) {
  return new Chart(ctx, {
      type: 'bar',
      data: data,
      options: {
        responsive: true,
        scales: {
            y: {                  
              beginAtZero: true,
              grid: {
                display: false,
              } 
            },
            x: {
              beginAtZero: true,
              grid: {
                display: false,
              },
              ticks: {
                // Rotate labels to be vertical
                maxRotation: 90,
                minRotation: 90
              }
            }
          }
      }
  });
}

//////////////////////////////

/**
 * Extracts and maps attributes from an array of arrays based on provided mappings.
 * @param {Array<Array>} data - The input data, where each element is an array of values.
 * @param {Object} mappedAttributes - An object mapping attribute names to column indices.
 * @returns {Array<Object>} - An array of objects, each containing the mapped attributes.
 */

export function extractMappedAttributes(data, mappedAttributes) {
  return data.map(subArray => {
    const result = {};

    // Extract columns based on provided mappings
    for (const [name, index] of Object.entries(mappedAttributes)) {
      result[name] = subArray[index];
    }
    return result;
  });
}

//////////////////////////////

/**
 * Aggregates data based on specified attributes, grouping keys, and optional date aggregation.
 * @param {Array<Object>} data - The input data, where each element is an object with various attributes.
 * @param {string} valueAttribute - The attribute whose values will be aggregated.
 * @param {Array<string>} groupKeys - An array of attributes to group the data by.
 * @param {Object} [dateAggregation] - Optional date aggregation, specifying a date key and level for aggregation.
 * @returns {Array<Object>} - An array of aggregated objects, each representing the grouped data with summed values.
 */

export function aggregateByAttributes(data, valueAttribute, groupKeys, dateAggregation) {
  if (data.length === 0 || !valueAttribute) return [];

  // Extract date key and level from dateAggregation if it exists
  const [dateKey, level] = dateAggregation ? Object.entries(dateAggregation)[0] : [undefined, undefined];

  // Aggregate data
  const aggregated = data.reduce((acc, item) => {
    // Get the start of the period for the date attribute if dateKey is defined
    const periodStart = dateKey ? getStartOfPeriod(item[dateKey], level) : '';

    // Create a key based on the group keys and the start of the period if dateAggregation is defined
    const groupKey = groupKeys
      ? [...groupKeys.map(key => item[key]), dateAggregation ? periodStart : ''].filter(Boolean).join('|')
      : periodStart;

    const attributeValue = item[valueAttribute];

    if (!acc[groupKey]) {
      acc[groupKey] = { ...groupKeys.reduce((obj, key) => ({ ...obj, [key]: item[key] }), {}), [valueAttribute]: 0 };
      if (dateKey) acc[groupKey][dateKey] = periodStart; // Add period start to result if dateKey is defined
    }
    acc[groupKey][valueAttribute] += attributeValue;

    return acc;
  }, {});

  // Transform aggregated data into array format
  return Object.values(aggregated);
}

//////////////////////////////

/**
 * Sorts an array of objects by a date field in ascending order.
 * @param {Object[]} data - Array of objects to sort.
 * @param {string} dateField - Name of the date field to sort by.
 * @returns {Object[]} Sorted array of objects.
 */

export function sortDataByDateField(data, dateField) {
  return data.slice().sort((a, b) => new Date(a[dateField]) - new Date(b[dateField]));
}

//////////////////////////////

/**
 * Sorts an array of objects by a number field.
 * @param {Object[]} data - Array of objects to sort.
 * @param {string} numberField - Name of the number field to sort by.
 * @param {string} [sortDirection=''] - Sort direction: 'Ascending', 'Descending', or ''.
 * @returns {Object[]} Sorted (or unsorted) array of objects.
 */
export function sortDataByNumberField(data, numberField, sortDirection = '') {
  if (sortDirection === 'Ascending') {
    return data.slice().sort((a, b) => a[numberField] - b[numberField]);
  } else if (sortDirection === 'Descending') {
    return data.slice().sort((a, b) => b[numberField] - a[numberField]);
  } else {
    return data; // Return the original data if sortDirection is ''
  }
}

//////////////////////////////

/**
 * Creates a dataset object for a chart with specified label and color.
 * @param {Array} data - Array of data points for the dataset.
 * @param {string} label - Label for the dataset.
 * @param {string} color - Border color for the dataset.
 * @returns {Object} Dataset object with label, data, borderColor, backgroundColor, and fill properties.
 */

export function createDataset(data, label, color) {
  return {
    label: label,
    data: data,
    borderColor: color,
    borderWidth: 2,
    backgroundColor: adjustRGBAAlpha(color, 0.7),
    fill: false,
  };
}

//////////////////////////////

/**
 * Groups and transforms data by a specified label into an array of x and y values.
 * @param {Array} data - Array of data objects to be transformed.
 * @param {string} x - Key for the x values in the data objects.
 * @param {string} y - Key for the y values in the data objects.
 * @param {string} legend - Key used for grouping data by label.
 * @returns {Object} An object where keys are labels and values are arrays of {x, y} objects.
 */

export function groupDataByLabel(data, x, y, legend) {
  return data.reduce((acc, item) => {
    // If the label is not yet a key in the accumulator, create an empty array for it
    if (!acc[item[legend]]) {
      acc[item[legend]] = [];
    }
    // Push the x and y values to the array corresponding to the label
    acc[item[legend]].push({ x: item[x], y: item[y] });
    return acc;
  }, {});
}

//////////////////////////////

/**
 * Filters an array of data objects based on label and date criteria.
 * @param {Array} data - Array of data objects to filter.
 * @param {Object} labelCriteria - Object specifying label key-value pairs for filtering.
 * @param {Object} dateCriteria - Object specifying date ranges for filtering, with keys as date fields and values as { start, end }.
 * @returns {Array} Filtered array of data objects that match the criteria.
 */

export function filterData(data, labelCriteria, dateCriteria) {
  return data.filter(item => {
    // Check label criteria
    const labelMatches = labelCriteria && Object.keys(labelCriteria).length > 0
      ? Object.entries(labelCriteria).every(([key, allowedValues]) => {
        return allowedValues.includes(item[key]);
      })
      : true; // If labelCriteria is undefined or empty, consider it a match

    // Check date criteria
    const dateMatches = dateCriteria && Object.keys(dateCriteria).length > 0
      ? Object.entries(dateCriteria).every(([key, dateRange]) => {
        const itemDate = new Date(item[key]);
        let matches = true;

        if (dateRange.start) {
          const startDate = new Date(dateRange.start);
          matches = matches && itemDate >= startDate; // Greater or equal to start
        }

        if (dateRange.end) {
          const endDate = new Date(dateRange.end);
          matches = matches && itemDate <= endDate; // Lower or equal to end
        }

        return matches;
      })
      : true; // If dateCriteria is undefined or empty, consider it a match

    return labelMatches && dateMatches;
  });
}

//////////////////////////////

/**
 * Picks a color from an array of color objects, optionally from the start or end of the array, or returns a random RGBA color if the array is empty.
 * @param {Object[]} colorArray - Array of color objects where each object has a single key-value pair representing a color.
 * @param {boolean} [reversed=false] - If true, picks the color from the last object in the array; otherwise, picks from the first object.
 * @returns {string} The color value from the selected color object in the array, or a random RGBA color if the array is empty.
 */

export function pickColor(colorArray, reversed = false) {
  // Ensure the colorArray is an array and has elements
  if (!Array.isArray(colorArray) || colorArray.length === 0) {
    return generateRandomRGBA(); // Return a random RGBA color
  }

  // Pick the color object based on the reversed flag
  const colorObject = reversed ? colorArray[colorArray.length - 1] : colorArray[0];
  const colorKey = Object.keys(colorObject)[0]; // Get the first key (color name)
  const colorValue = colorObject[colorKey]; // Get the color value

  // Remove the color object from the colorArray array
  colorArray.splice(reversed ? colorArray.length - 1 : 0, 1);

  return colorValue; // Return the color value
}

//////////////////////////////