-- =============================================================
-- Returns tables for WB, Ozon, Yandex Market
-- Run in Supabase SQL Editor (dashboard.supabase.com)
-- =============================================================

-- WB Returns
CREATE TABLE IF NOT EXISTS public.returns_wb (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id             UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
    srid                TEXT NOT NULL,
    order_dt            TIMESTAMPTZ,
    nm_id               BIGINT,
    brand               TEXT,
    subject_name        TEXT,
    tech_size           TEXT,
    barcode             TEXT,
    shk_id              BIGINT,
    return_type         TEXT,
    reason              TEXT,
    status              TEXT,
    is_status_active    BOOLEAN,
    ready_to_return_dt  TIMESTAMPTZ,
    completed_dt        TIMESTAMPTZ,
    expired_dt          TIMESTAMPTZ,
    dst_office_id       INT,
    dst_office_address  TEXT,
    order_id            BIGINT,
    sticker_id          BIGINT,
    user_status         TEXT,
    user_comment        TEXT,
    synced_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(srid, shop_id)
);

-- Ozon Returns
CREATE TABLE IF NOT EXISTS public.returns_ozon (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id        UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
    posting_number TEXT NOT NULL,
    added_at       TIMESTAMPTZ,
    barcode        TEXT,
    clearing_id    BIGINT,
    offer_id       TEXT,
    status         TEXT,
    return_reason  TEXT,
    return_date    TIMESTAMPTZ,
    received_at    TIMESTAMPTZ,
    quantity       INT,
    price          NUMERIC,
    is_opened      BOOLEAN,
    user_status    TEXT,
    user_comment   TEXT,
    synced_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(posting_number, shop_id)
);

-- Yandex Market Returns
CREATE TABLE IF NOT EXISTS public.returns_ym (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id                 UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
    ym_return_id            BIGINT NOT NULL,
    order_id                BIGINT,
    return_type             TEXT,
    shipment_status         TEXT,
    refund_status           TEXT,
    creation_date           TIMESTAMPTZ,
    update_date             TIMESTAMPTZ,
    pickup_till_date        TIMESTAMPTZ,
    amount                  NUMERIC,
    currency                TEXT,
    shipment_recipient_type TEXT,
    logistic_point          TEXT,
    items                   JSONB,
    user_status             TEXT,
    user_comment            TEXT,
    synced_at               TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ym_return_id, shop_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_returns_wb_shop_dt ON public.returns_wb (shop_id, order_dt DESC);
CREATE INDEX IF NOT EXISTS idx_returns_wb_shop_status ON public.returns_wb (shop_id, status);
CREATE INDEX IF NOT EXISTS idx_returns_wb_shop_barcode ON public.returns_wb (shop_id, barcode);

CREATE INDEX IF NOT EXISTS idx_returns_ozon_shop_dt ON public.returns_ozon (shop_id, return_date DESC);
CREATE INDEX IF NOT EXISTS idx_returns_ozon_shop_status ON public.returns_ozon (shop_id, status);
CREATE INDEX IF NOT EXISTS idx_returns_ozon_shop_sku ON public.returns_ozon (shop_id, offer_id);

CREATE INDEX IF NOT EXISTS idx_returns_ym_shop_dt ON public.returns_ym (shop_id, creation_date DESC);
CREATE INDEX IF NOT EXISTS idx_returns_ym_shop_status ON public.returns_ym (shop_id, shipment_status);

-- RLS
-- Service role (backend) bypasses RLS automatically.
-- Anon/authenticated frontend users see only their own rows.
ALTER TABLE public.returns_wb ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.returns_ozon ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.returns_ym ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own rows" ON public.returns_wb
    FOR ALL USING (shop_id IN (SELECT id FROM public.shops WHERE user_id = auth.uid()));

CREATE POLICY "own rows" ON public.returns_ozon
    FOR ALL USING (shop_id IN (SELECT id FROM public.shops WHERE user_id = auth.uid()));

CREATE POLICY "own rows" ON public.returns_ym
    FOR ALL USING (shop_id IN (SELECT id FROM public.shops WHERE user_id = auth.uid()));
