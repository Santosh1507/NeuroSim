-- MiroFish Supabase Schema
-- Run this in the Supabase SQL Editor after creating your project

-- 1. Projects table
CREATE TABLE IF NOT EXISTS projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  title TEXT,
  status TEXT DEFAULT 'created',
  simulation_requirement TEXT,
  graph_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own their projects" ON projects
  FOR ALL USING (auth.uid() = user_id);

-- 2. Project files
CREATE TABLE IF NOT EXISTS project_files (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_name TEXT,
  file_type TEXT,
  storage_path TEXT,
  size_bytes BIGINT,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE project_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own their files" ON project_files
  FOR ALL USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
  );

-- 3. Simulation runs
CREATE TABLE IF NOT EXISTS simulation_runs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  simulation_id TEXT,
  config JSONB,
  status TEXT DEFAULT 'created',
  result_summary TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE simulation_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own their simulations" ON simulation_runs
  FOR ALL USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
  );

-- 4. Reports
CREATE TABLE IF NOT EXISTS reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  simulation_run_id UUID REFERENCES simulation_runs(id) ON DELETE CASCADE,
  report_id TEXT,
  status TEXT DEFAULT 'generating',
  content JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own their reports" ON reports
  FOR ALL USING (
    simulation_run_id IN (
      SELECT sr.id FROM simulation_runs sr
      JOIN projects p ON sr.project_id = p.id
      WHERE p.user_id = auth.uid()
    )
  );

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_project_id ON simulation_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_reports_simulation_run_id ON reports(simulation_run_id);
