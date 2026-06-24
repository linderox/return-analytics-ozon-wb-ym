# Supabase Setup

## 1. Create Tables

Run the following SQL in the Supabase SQL editor:

```sql
-- 1. profiles table (one row per user)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL DEFAULT 'free',
    is_admin BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. shops table (marketplace connections)
CREATE TABLE public.shops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    marketplace TEXT NOT NULL CHECK (marketplace IN ('wb', 'ozon', 'ym')),
    name TEXT,
    wb_token TEXT,
    ozon_client_id TEXT,
    ozon_client_secret TEXT,
    ym_token TEXT,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. subscriptions table (billing)
CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    yookassa_id TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- profiles: users see only their own row
CREATE POLICY "profiles_own" ON public.profiles
    FOR ALL USING (auth.uid() = id);

-- shops: users see only their own shops
CREATE POLICY "shops_own" ON public.shops
    FOR ALL USING (auth.uid() = user_id);

-- subscriptions: users see only their own
CREATE POLICY "subscriptions_own" ON public.subscriptions
    FOR ALL USING (auth.uid() = user_id);

-- Auto-create profile row when a user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id) VALUES (NEW.id) ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

## 2. Add Users via Authentication

Create users through the Supabase Authentication dashboard (or via the API).

## 3. Backfill Existing Auth Users into Profiles

After adding users to Authentication, run this to populate the `profiles` table for any existing users (skips duplicates):

```sql
-- Insert all existing auth users into profiles (skips duplicates)
INSERT INTO public.profiles (id)
SELECT id FROM auth.users
ON CONFLICT DO NOTHING;
```
