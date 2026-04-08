/**
 * Global Frontend Configuration
 * Centralizes all environment variables and constants.
 */

const config = {
    // Branding
    APP_NAME: import.meta.env.VITE_APP_NAME || "Mentor::i",

    // API Endpoints
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8766",

    // Feature Flags / Limits
    MAX_TOKEN_LIMIT: 50000, // Threshold for Red badge
    WARN_TOKEN_LIMIT: 10000, // Threshold for Yellow badge
};

export default config;
