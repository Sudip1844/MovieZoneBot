// MovieZone Redirect Page JavaScript - Updated & Final Version

// --- Configuration ---
const COUNTDOWN_SECONDS = 10; // Timer duration in seconds (changed from 15 to 10)
const BOT_USERNAME = "MoviezoneDownloadbot"; // Your actual bot username

// --- Global Variables ---
let countdown = COUNTDOWN_SECONDS;
let timerInterval;
let secureToken = ''; // The unique token from the bot

document.addEventListener('DOMContentLoaded', initializePage);

/**
 * Initializes the page on load.
 * - Extracts the token from URL parameters.
 * - Starts the timer.
 * - Sets up event listeners.
 */
function initializePage() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        secureToken = urlParams.get('token');
        const userId = urlParams.get('uid');

        if (!secureToken || !userId) {
            showError("Invalid or missing link parameters. Please get a new download link from the bot.");
            return;
        }

        console.log(`Token: ${secureToken}, UserID: ${userId}`);

        startTimer();
        setupEventListeners();

    } catch (error) {
        console.error('Error initializing page:', error);
        showError('An unexpected error occurred while loading the page.');
    }
}

/**
 * Displays an error message and hides the main content.
 * @param {string} message - The error message to display.
 */
function showError(message) {
    const botLink = `https://t.me/${BOT_USERNAME}`;
    const errorHtml = `
        <div style="text-align: center; padding: 50px; color: white; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <h2 style="color: #ff4d4d; font-size: 2em;">❌ Error</h2>
            <p style="font-size: 1.2rem; margin: 20px 0;">${message}</p>
            <a href="${botLink}" style="display: inline-block; background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin-top: 20px;">
                🔙 Return to Bot
            </a>
        </div>
    `;
    document.body.innerHTML = errorHtml;
}

/**
 * Sets up event listeners for the interactive buttons.
 */
function setupEventListeners() {
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.addEventListener('click', handleContinueToBot);
    }

    const scrollBtn = document.getElementById('scrollToBottomBtn');
    if (scrollBtn) {
        scrollBtn.addEventListener('click', (e) => {
            e.preventDefault();
            smoothScrollToBottom();
        });
    }
}

/**
 * Starts the 15-second countdown timer.
 */
function startTimer() {
    const timerText = document.getElementById('timerText');
    const timerSeconds = document.getElementById('timerSeconds');

    timerInterval = setInterval(() => {
        countdown--;

        if (timerText) timerText.textContent = countdown;
        if (timerSeconds) timerSeconds.textContent = countdown;

        if (countdown <= 0) {
            clearInterval(timerInterval);
            onTimerComplete();
        }
    }, 1000);
}

/**
 * Executes when the timer finishes.
 * Hides the timer and shows the scroll/continue buttons.
 * Auto-scrolls to bottom after 3 seconds if user doesn't interact.
 */
function onTimerComplete() {
    // Hide timer section
    const timerSection = document.getElementById('timerSection');
    if (timerSection) {
        timerSection.style.display = 'none';
    }

    // Show "Scroll to Bottom" button
    const scrollButtonContainer = document.getElementById('scrollButtonContainer');
    if (scrollButtonContainer) {
        scrollButtonContainer.style.display = 'block';
    }

    // Show the final "Continue" button at the bottom of the page
    const downloadSection = document.getElementById('downloadSection');
    if (downloadSection) {
        downloadSection.style.display = 'block';
    }
    
    // Auto-scroll after 3 seconds if user doesn't manually scroll
    setTimeout(() => {
        const continueBtn = document.getElementById('continueBtn');
        if (continueBtn && !continueBtn.hasAttribute('data-user-scrolled')) {
            smoothScrollToBottom();
            
            // Auto-click continue button after another 3 seconds if user doesn't click
            setTimeout(() => {
                if (continueBtn && !continueBtn.hasAttribute('data-clicked')) {
                    handleContinueToBot();
                }
            }, 3000);
        }
    }, 3000);
}

/**
 * Smoothly scrolls the page to the bottom.
 */
function smoothScrollToBottom() {
    const downloadSection = document.getElementById('downloadSection');
    const continueBtn = document.getElementById('continueBtn');
    
    // Mark that user has scrolled (or auto-scroll occurred)
    if (continueBtn) {
        continueBtn.setAttribute('data-user-scrolled', 'true');
    }
    
    if (downloadSection) {
        downloadSection.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    } else {
        // Fallback if the element is not found
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    }
}

/**
 * Handles the final "Continue to Bot" button click.
 * Generates the secure deep link and redirects the user back to the bot.
 */
function handleContinueToBot() {
    if (!secureToken) {
        alert('Error: Token is missing. Cannot return to bot.');
        return;
    }

    const continueBtn = document.getElementById('continueBtn');
    
    // Mark button as clicked to prevent auto-click
    if (continueBtn) {
        continueBtn.setAttribute('data-clicked', 'true');
        continueBtn.textContent = 'Returning to bot...';
        continueBtn.disabled = true;
    }

    // This is the updated, secure return URL.
    // It sends only the token back to the bot.
    const returnUrl = `https://t.me/${BOT_USERNAME}?start=${secureToken}`;

    // Redirect the user
    window.location.href = returnUrl;

    // Optional: Show a final success message before the redirect happens
    setTimeout(() => {
        if (continueBtn) {
            continueBtn.textContent = 'Success!';
        }
    }, 500);
}
