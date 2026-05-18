import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const isConfigured = supabaseUrl.length > 0 && supabaseAnonKey.length > 0

export const supabase = isConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null

export { isConfigured as isSupabaseConfigured }
