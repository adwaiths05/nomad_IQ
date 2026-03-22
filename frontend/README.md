# Nomadiq - AI Travel Planner Frontend

A modern React/Next.js frontend for Nomadiq, an AI-powered travel planning application. This application provides a comprehensive interface for users to plan trips, create itineraries, chat with an AI assistant, and explore travel guides.

## Features

- **User Authentication**: Secure login and registration with JWT-based authentication
- **Trip Management**: Create, view, and manage multiple trips with custom details
- **Itinerary Planning**: Build day-by-day itineraries with activities, locations, and timing
- **AI Travel Assistant**: Chat with an AI assistant for travel recommendations and advice
- **Travel Guides**: Browse curated travel guides with destination information and tips
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS and shadcn/ui components
- **Real-time Updates**: Automatic data synchronization with the backend API

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui
- **State Management**: React Context API
- **HTTP Client**: Native Fetch API
- **Icons**: Lucide React

## Project Structure

```
├── app/                           # Next.js app directory
│   ├── (auth)/                   # Authentication pages (login, register)
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── dashboard/            # Main dashboard
│   │   ├── trips/                # Trip management
│   │   ├── itinerary/            # Itinerary management
│   │   ├── chat/                 # AI chat interface
│   │   └── guides/               # Travel guides
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Landing page
│   └── globals.css               # Global styles
├── components/                    # React components
│   ├── ui/                       # shadcn/ui components
│   ├── dashboard/                # Dashboard-specific components
│   ├── error-boundary.tsx        # Error boundary component
│   └── protected-route.tsx       # Protected route wrapper
├── lib/                          # Utility libraries
│   ├── api/                      # API client and types
│   │   ├── client.ts            # API client class
│   │   └── types.ts             # TypeScript interfaces
│   ├── context/                  # React Context
│   │   └── auth-context.tsx     # Authentication context
│   ├── utils/                    # Utility functions
│   │   └── errors.ts            # Error handling utilities
│   └── config.ts                # Configuration file
└── package.json                  # Dependencies
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm, yarn, or pnpm

### Installation

1. **Install dependencies**:
```bash
npm install
# or
pnpm install
```

2. **Set up environment variables**:

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Replace the URL with your backend API endpoint:
- For local development: `http://localhost:8000/api`
- For production: `https://api.yourdomain.com/api`

### Running the Application

**Development mode**:
```bash
npm run dev
# or
pnpm dev
```

The application will start at `http://localhost:3000`

**Production build**:
```bash
npm run build
npm start
```

## API Integration

The frontend communicates with the Nomadiq backend API. The API client is located in `/lib/api/client.ts` and provides methods for:

### Authentication
- `login(email, password)` - User login
- `register(username, email, password)` - User registration
- `logout()` - User logout

### Trips
- `getAll()` - Fetch all user trips
- `getById(tripId)` - Fetch specific trip
- `create(tripData)` - Create new trip
- `update(tripId, tripData)` - Update trip
- `delete(tripId)` - Delete trip

### Itinerary
- `getByTrip(tripId)` - Fetch itinerary for a trip
- `create(itemData)` - Add activity to itinerary
- `update(itemId, itemData)` - Update activity
- `delete(itemId)` - Delete activity

### Chat
- `getMessages(tripId)` - Fetch chat history
- `sendMessage(tripId, message)` - Send message to AI

### Guides
- `getAll()` - Fetch all travel guides
- `getById(guideId)` - Fetch specific guide

## Authentication Flow

1. User visits the landing page
2. User clicks "Sign In" or "Register"
3. Credentials are sent to the backend API
4. JWT token is received and stored in localStorage
5. User is redirected to the dashboard
6. Protected routes check for valid token
7. All subsequent API requests include the Authorization header

## Error Handling

The application includes comprehensive error handling:

- **API Errors**: Caught and displayed as toast notifications
- **Network Errors**: Handled with user-friendly messages
- **Validation Errors**: Form validation before submission
- **Error Boundary**: React error boundary for component errors

## Configuration

Configuration is managed in `/lib/config.ts`:

```typescript
export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
    timeout: 30000,
  },
  storage: {
    token: 'nomadiq_token',
    user: 'nomadiq_user',
  },
  features: {
    aiChat: true,
    guides: true,
    itinerary: true,
  },
}
```

## Deployment

### Deploy to Vercel

1. Push your code to GitHub
2. Import the project in Vercel
3. Add environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

### Deploy to Other Platforms

1. Build the project: `npm run build`
2. Deploy the `.next` folder and dependencies to your hosting

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api` |

## Development Tips

- **Debug API Calls**: Check browser DevTools Network tab
- **Local Storage**: Authentication token stored in localStorage
- **TypeScript**: Type definitions prevent runtime errors
- **Component Reusability**: Use shadcn/ui components for consistency

## Troubleshooting

### API Connection Issues
- Ensure backend is running on the correct port
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify CORS settings on backend

### Authentication Issues
- Clear browser cache and localStorage
- Check token expiration in localStorage
- Verify backend authentication endpoint

### Build Errors
- Delete `.next` folder and rebuild
- Clear node_modules and reinstall
- Check Node.js version compatibility

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues or questions, please contact the development team or create an issue on GitHub.

---

**Last Updated**: March 2026
**Version**: 1.0.0
