import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ModelsPage } from '@/pages/ModelsPage'

describe('ModelsPage', () => {
  it('renders the page title', () => {
    render(<ModelsPage />)
    expect(screen.getByText('Model Providers')).toBeInTheDocument()
  })

  it('renders the Add Provider button', () => {
    render(<ModelsPage />)
    expect(screen.getByText('Add Provider')).toBeInTheDocument()
  })

  it('renders all 3 provider cards', () => {
    render(<ModelsPage />)
    // Provider name appears as h3 and also as type label (p), so use getAllByText
    expect(screen.getAllByText('Anthropic').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('OpenAI').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('DeepSeek').length).toBeGreaterThanOrEqual(1)
  })

  it('displays base URLs for each provider', () => {
    render(<ModelsPage />)
    expect(screen.getByText('https://api.anthropic.com')).toBeInTheDocument()
    expect(screen.getByText('https://api.openai.com/v1')).toBeInTheDocument()
    expect(screen.getByText('https://api.deepseek.com/v1')).toBeInTheDocument()
  })

  it('shows configured status for providers with keys', () => {
    render(<ModelsPage />)
    const configured = screen.getAllByText('Configured')
    expect(configured).toHaveLength(2)
  })

  it('shows not configured status for providers without keys', () => {
    render(<ModelsPage />)
    expect(screen.getByText('Not configured')).toBeInTheDocument()
  })

  it('displays available models for each provider', () => {
    render(<ModelsPage />)
    expect(screen.getByText('claude-opus-4-7')).toBeInTheDocument()
    expect(screen.getByText('claude-sonnet-4-6')).toBeInTheDocument()
    expect(screen.getByText('gpt-4o')).toBeInTheDocument()
    expect(screen.getByText('deepseek-chat')).toBeInTheDocument()
  })

  it('renders Update Key buttons', () => {
    render(<ModelsPage />)
    const buttons = screen.getAllByText('Update Key')
    expect(buttons).toHaveLength(3)
  })

  it('displays model tags in monospace style', () => {
    render(<ModelsPage />)
    const tag = screen.getByText('claude-opus-4-7')
    expect(tag).toHaveClass('font-mono')
  })
})
