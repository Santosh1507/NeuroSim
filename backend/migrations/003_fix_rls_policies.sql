-- Fix RLS policies to prevent unauthenticated access to all data
-- Previously: auth.uid()::text = user_id OR user_id = 'anonymous' allowed ANY unauthenticated user to read ALL rows
-- Now: unauthenticated users can only read rows where user_id = 'anonymous'

-- Videos table
DROP POLICY IF EXISTS "Users can read own videos" ON videos;
CREATE POLICY "Users can read own videos"
    ON videos FOR SELECT
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

-- Analyses table
DROP POLICY IF EXISTS "Users can read own analyses" ON analyses;
CREATE POLICY "Users can read own analyses"
    ON analyses FOR SELECT
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

-- AB tests table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'ab_tests') THEN
        DROP POLICY IF EXISTS "Users can read own ab_tests" ON ab_tests;
        CREATE POLICY "Users can read own ab_tests"
            ON ab_tests FOR SELECT
            USING (
                (auth.uid() IS NULL AND user_id = 'anonymous')
                OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
            );
    END IF;
END $$;
