/**
 * Error handling utilities
 */

export class AppError extends Error {
  public code: string
  public statusCode: number
  public isOperational: boolean

  constructor(
    message: string,
    code: string = 'INTERNAL_ERROR',
    statusCode: number = 500,
    isOperational: boolean = true
  ) {
    super(message)
    this.code = code
    this.statusCode = statusCode
    this.isOperational = isOperational

    Error.captureStackTrace(this, this.constructor)
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR', 400, true)
  }
}

export class NotFoundError extends AppError {
  constructor(message: string = 'Resource not found') {
    super(message, 'NOT_FOUND', 404, true)
  }
}

export class UnauthorizedError extends AppError {
  constructor(message: string = 'Unauthorized') {
    super(message, 'UNAUTHORIZED', 401, true)
  }
}

export class ForbiddenError extends AppError {
  constructor(message: string = 'Forbidden') {
    super(message, 'FORBIDDEN', 403, true)
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409, true)
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof AppError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}

export function isOperationalError(error: unknown): boolean {
  if (error instanceof AppError) {
    return error.isOperational
  }
  return false
}
