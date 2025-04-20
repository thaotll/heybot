# HeyBot Frontend

A Next.js frontend for the HeyBot project.

## Setup Instructions

Follow these steps to get the frontend running locally:

1. **Install dependencies**:
   ```bash
   npm install --legacy-peer-deps
   ```
   Note: We use `--legacy-peer-deps` to handle some package compatibility issues.

2. **Run the development server**:
   ```bash
   npm run dev
   ```
   The app will be available at [http://localhost:3030](http://localhost:3030) with turbopack enabled.

3. **Build for production**:
   ```bash
   npm run build
   ```

4. **Start production server**:
   ```bash
   npm start
   ```

## Troubleshooting

If you encounter any issues:

1. Make sure you're using the `--legacy-peer-deps` flag when installing due to some package version conflicts.
2. If you have problems with the build cache, try deleting the `.next` folder and rebuilding.
3. Ensure all environment variables are properly set (copy from `.env.example` if available).
4. **CRITICAL: Make sure you have these directories from the repository:**
   - `/lib` - Contains essential utility functions and server actions
   - `/components` - Contains all UI components
   - `/app` - Contains the Next.js application routes
   - `/hooks` - Contains custom React hooks
   
   If any of these directories are missing, the application will not function properly. Check that Git pulled them correctly.

## Project Structure

- `app/` - Next.js app router files
- `components/` - Reusable UI components
- `hooks/` - Custom React hooks
- `lib/` - Utility functions and shared code
- `public/` - Static assets
- `styles/` - Global styles and CSS modules 