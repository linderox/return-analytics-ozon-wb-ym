-- Run this in Supabase SQL Editor to fix the schema for the application

-- 1. Update profiles table
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS fio TEXT,
ADD COLUMN IF NOT EXISTS phone TEXT;

-- 2. Update shops table
ALTER TABLE public.shops
ADD COLUMN IF NOT EXISTS ozon_performance_client_id TEXT,
ADD COLUMN IF NOT EXISTS ozon_performance_client_secret TEXT,
ADD COLUMN IF NOT EXISTS ym_client_id TEXT,
ADD COLUMN IF NOT EXISTS ym_client_secret TEXT,
ADD COLUMN IF NOT EXISTS ym_campaign_id TEXT,
ADD COLUMN IF NOT EXISTS fulfillment_models JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS status_filter JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS schema_filter JSONB DEFAULT '[]'::jsonb;

-- Sync ym_token to ym_client_id if needed
UPDATE public.shops SET ym_client_id = ym_token WHERE ym_client_id IS NULL AND ym_token IS NOT NULL;
