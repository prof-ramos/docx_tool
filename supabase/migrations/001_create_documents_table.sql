-- Create vector extension
create extension if not exists vector with schema extensions;

-- Create documents table with vector embeddings
create table if not exists public.documents (
    id text primary key,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create index for vector similarity search
create index if not exists documents_embedding_idx on public.documents
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Create index for metadata queries
create index if not exists documents_metadata_idx on public.documents using gin(metadata);

-- Create function for vector similarity search
create or replace function match_documents (
  query_embedding vector(1536),
  match_threshold float default 0.7,
  match_count int default 5
)
returns table (
  id text,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Create function to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Create trigger for updated_at
create trigger update_documents_updated_at before update on public.documents
    for each row execute procedure update_updated_at_column();

-- Enable Row Level Security
alter table public.documents enable row level security;

-- Create policy to allow read access
create policy "Allow public read access" on public.documents
    for select using (true);

-- Create policy to allow authenticated insert/update
create policy "Allow authenticated insert" on public.documents
    for insert with check (auth.role() = 'authenticated' or auth.role() = 'service_role');

create policy "Allow authenticated update" on public.documents
    for update using (auth.role() = 'authenticated' or auth.role() = 'service_role');

-- Create stats view for admin dashboard
create or replace view public.document_stats as
select
    count(*) as total_documents,
    count(distinct metadata->>'source') as total_sources,
    count(distinct metadata->>'title') as unique_titles,
    max(created_at) as last_ingestion,
    pg_size_pretty(pg_total_relation_size('public.documents')) as table_size
from public.documents;

-- Grant access to stats view
grant select on public.document_stats to anon, authenticated;

-- Create function to get document statistics
create or replace function get_document_statistics()
returns json
language plpgsql
as $$
declare
    result json;
begin
    select json_build_object(
        'total_documents', count(*),
        'total_sources', count(distinct metadata->>'source'),
        'unique_titles', count(distinct metadata->>'title'),
        'last_ingestion', max(created_at),
        'sources_breakdown', (
            select json_object_agg(source, count)
            from (
                select
                    metadata->>'source' as source,
                    count(*) as count
                from public.documents
                group by metadata->>'source'
            ) as sources
        )
    ) into result
    from public.documents;

    return result;
end;
$$;

-- Grant execute on statistics function
grant execute on function get_document_statistics() to anon, authenticated;

-- Create index on created_at for faster sorting
create index if not exists documents_created_at_idx on public.documents(created_at desc);

-- Add comment to table
comment on table public.documents is 'Legal documents with vector embeddings for RAG';
comment on column public.documents.embedding is 'OpenAI text-embedding-3-small (1536 dimensions)';
comment on function match_documents is 'Search for similar documents using cosine similarity';
