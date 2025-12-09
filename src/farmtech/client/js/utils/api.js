/**
 * API Utility Module
 * Provides HTTP methods with automatic authentication and error handling
 * Similar to axios but using native fetch
 */

import { getCookie } from './helpers';

/**
 * Get CSRF token from cookies
 * @returns {string|null} CSRF token
 */
const getCsrfToken = () => {
    return getCookie('csrftoken');
};

/**
 * Default configuration for API requests
 */
const defaultConfig = {
    credentials: 'include', // Always include cookies
    headers: {
        'Content-Type': 'application/json',
    }
};

/**
 * Build headers with CSRF token for write operations
 * @param {Object} customHeaders - Custom headers to merge
 * @param {boolean} includeContentType - Whether to include Content-Type header
 * @returns {Object} Headers object
 */
const buildHeaders = (customHeaders = {}, includeContentType = true) => {
    const headers = { ...customHeaders };

    const csrfToken = getCsrfToken();
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;        
    }

    if (includeContentType && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    return headers;
};

/**
 * Handle API response
 * @param {Response} response - Fetch response object
 * @returns {Promise} Parsed JSON or error
 */
const handleResponse = async (response) => {
    // Check if response has content
    const contentType = response.headers.get('content-type');
    const hasJson = contentType && contentType.includes('application/json');

    const data = hasJson ? await response.json() : await response.text();

    if (!response.ok) {
        const error = new Error(data.message || data.detail || 'API request failed');
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
};

/**
 * GET request
 * @param {string} url - API endpoint
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Response data
 */
export const get = async (url, options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'GET',
        headers: buildHeaders(options.headers, false),
    };

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * POST request
 * @param {string} url - API endpoint
 * @param {Object} data - Request body
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Response data
 */
export const post = async (url, data = null, options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'POST',
        headers: buildHeaders(options.headers),
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * PUT request
 * @param {string} url - API endpoint
 * @param {Object} data - Request body
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Response data
 */
export const put = async (url, data = null, options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'PUT',
        headers: buildHeaders(options.headers),
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * PATCH request
 * @param {string} url - API endpoint
 * @param {Object} data - Request body
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Response data
 */
export const patch = async (url, data = null, options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'PATCH',
        headers: buildHeaders(options.headers),
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * DELETE request
 * @param {string} url - API endpoint
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Response data
 */
export const del = async (url, options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'DELETE',
        headers: buildHeaders(options.headers, false),
    };

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * POST request with FormData (for file uploads)
 * @param {string} url - API endpoint
 * @param {FormData} formData - FormData object
 * @param {Object} options - Additional fetch options
 * @param {Function} onProgress - Progress callback (receives percentage)
 * @returns {Promise} Response data
 */
export const postFormData = async (url, formData, options = {}, onProgress = null) => {
    // If progress callback is provided, use XMLHttpRequest for upload progress tracking
    if (onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    onProgress(percentComplete);
                }
            });

            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const contentType = xhr.getResponseHeader('content-type');
                        const hasJson = contentType && contentType.includes('application/json');
                        const data = hasJson ? JSON.parse(xhr.responseText) : xhr.responseText;
                        resolve(data);
                    } catch (error) {
                        reject(new Error('Failed to parse response'));
                    }
                } else {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        const error = new Error(data.message || data.detail || 'API request failed');
                        error.status = xhr.status;
                        error.data = data;
                        reject(error);
                    } catch (e) {
                        reject(new Error(`Request failed with status ${xhr.status}`));
                    }
                }
            });

            // Handle errors
            xhr.addEventListener('error', () => {
                reject(new Error('Network error occurred'));
            });

            xhr.addEventListener('abort', () => {
                reject(new Error('Request aborted'));
            });

            // Open and send request
            xhr.open('POST', url);

            // Set headers
            const headers = buildHeaders(options.headers || {}, false);
            Object.keys(headers).forEach(key => {
                xhr.setRequestHeader(key, headers[key]);
            });

            // Set credentials
            xhr.withCredentials = true;

            xhr.send(formData);
        });
    }

    // Fallback to fetch if no progress callback
    const config = {
        ...defaultConfig,
        ...options,
        method: 'POST',
        // Don't set Content-Type for FormData, browser will set it with boundary
        headers: buildHeaders(options.headers, false),
    };

    config.body = formData;

    const response = await fetch(url, config);
    return handleResponse(response);
};

/**
 * Download file from API endpoint
 * @param {string} url - API endpoint
 * @param {string} filename - Default filename if not provided by server
 * @param {Object} options - Additional fetch options
 * @returns {Promise<void>}
 */
export const downloadFile = async (url, filename = 'download', options = {}) => {
    const config = {
        ...defaultConfig,
        ...options,
        method: 'GET',
        headers: buildHeaders(options.headers, false),
    };

    const response = await fetch(url, config);

    if (!response.ok) {
        const contentType = response.headers.get('content-type');
        const hasJson = contentType && contentType.includes('application/json');
        const data = hasJson ? await response.json() : await response.text();

        const error = new Error(data.message || data.detail || 'Download failed');
        error.status = response.status;
        error.data = data;
        throw error;
    }

    // Get filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('Content-Disposition');
    let downloadFilename = filename;

    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
            downloadFilename = filenameMatch[1].replace(/['"]/g, '');
        }
    }

    // Create blob and download
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = downloadFilename;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
};

/**
 * Default export with all methods
 */
export default {
    get,
    post,
    put,
    patch,
    delete: del,
    postFormData,
    downloadFile
};
