# Google Scholar Import Feature - User Guide

## Overview

The admin panel now includes an automated Google Scholar import feature that allows you to update your portfolio with all publications from your Google Scholar profile with just a few clicks.

## How to Use

### Step 1: Access the Import Page

You can access the Google Scholar import feature in two ways:

1. **From the Dashboard:**
   - Login to admin panel at http://localhost:5000/admin/login
   - Click the "Import from Scholar" button in the Quick Actions section

2. **From Publications Management:**
   - Go to Admin → Publications
   - Click the "Import from Scholar" button in the header

### Step 2: Enter Your Google Scholar URL

1. Go to your Google Scholar profile page
2. Copy the URL from your browser's address bar
   - Example: `https://scholar.google.com/citations?user=j3B8Dz8AAAAJ&hl=en`
3. Paste the URL into the input field on the import page

### Step 3: Import Publications

1. Click the "Import Publications" button
2. Wait for the scraper to fetch and process your publications (this may take 10-30 seconds)
3. Review the results showing:
   - Total publications found
   - Number of new publications added
   - Number of duplicates skipped
   - Detailed list of all publications processed

## Features

### Automatic Data Extraction

The scraper automatically extracts:
- **Title** - Full publication title
- **Authors** - All author names
- **Venue** - Journal or conference name
- **Year** - Publication year
- **Citations** - Current citation count
- **Google Scholar Link** - Direct link to the publication on Google Scholar

### Smart Duplicate Detection

- Publications are checked against existing entries by title
- Duplicates are automatically skipped to prevent redundant entries
- You'll see a summary of how many were added vs. skipped

### Auto-Categorization

Publications are automatically assigned to research areas based on keywords:

- **Machine Learning** - Keywords: machine learning, ML, deep learning, neural, AI
- **Data Science** - Keywords: data, analytics, analysis, statistical
- **Business Analytics** - Keywords: business, management, decision, enterprise, performance
- **Information Technology** - Keywords: information, technology, system, software, IoT, blockchain, cloud

### Real-Time Results

After import, you'll see:
- ✅ Green checkmarks for newly added publications
- ⊖ Gray indicators for skipped duplicates
- Complete list with titles and years

## Tips

1. **First Time Import:** Your first import will add all publications from your profile
2. **Regular Updates:** Run the import periodically to update citation counts and add new publications
3. **Manual Editing:** After import, you can edit any publication to add abstracts, PDFs, or thumbnails
4. **URL Format:** Make sure to use the full Google Scholar profile URL including the user ID

## Troubleshooting

**"No publications found"**
- Verify your Google Scholar profile is public
- Check that the URL is correct and complete
- Make sure you're using the profile URL, not a search results page

**"Error scraping Google Scholar"**
- Check your internet connection
- Google Scholar may be temporarily unavailable
- Try again in a few minutes

**"Duplicates skipped"**
- This is normal if you've already imported these publications
- Only new publications will be added
- Existing publications won't be modified

## Technical Details

### Files Involved

- `scholar_utils.py` - Core scraping and categorization logic
- `app.py` - Flask route handler for `/admin/import-scholar`
- `templates/admin/import_scholar.html` - User interface
- `templates/admin/dashboard.html` - Dashboard with import link
- `templates/admin/publications.html` - Publications page with import link

### Security

- Import feature requires admin authentication
- Only accessible to logged-in admin users
- URL validation prevents malicious inputs
- Database transactions ensure data integrity

## Future Enhancements

Potential improvements for future versions:
- Automatic citation count updates for existing publications
- Scheduled imports to keep data fresh
- Import from other sources (ORCID, ResearchGate, etc.)
- Bulk editing of imported publications
