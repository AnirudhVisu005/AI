import { FormEvent, useEffect, useMemo, useState, useRef } from 'react';
import {
  Send,
  Settings,
  BookOpen,
  AlertCircle,
  Bot,
  User,
  CheckCircle,
  Zap,
  BarChart2,
  Trash2,
  Edit2,
  X,
} from 'lucide-react';

type ChatRole = 'assistant' | 'user';

type ChatMessage = {
  id: number;
  role: ChatRole;
  text: string;
  steps?: string[];
  reference?: string;
  sourceType?: string;
};

type SupportResponse = {
  answer: string;
  steps: string[];
  reference?: string;
  source_type: string;
};

type FaqRecord = {
  id: number;
  question: string;
  answer: string;
  tags: string;
  page: string;
};

type ErrorRecord = {
  id: number;
  error_key: string;
  message: string;
  fix: string;
  page: string;
};

type ManualRecord = {
  id: number;
  title: string;
  content: string;
  tags: string;
  page: string;
};

type AnalyticsData = {
  total_questions: number;
  top_questions: { question: string; count: number }[];
  by_page: { page: string; count: number }[];
};

const pageOptions = ['Dashboard', 'Upload Page', 'Reports', 'Settings'];

const quickPrompts = [
  { label: 'Upload Help', prompt: 'How do I upload a file?', icon: <Zap size={16} /> },
  { label: 'Report Issue', prompt: 'I am seeing an error while uploading.', icon: <AlertCircle size={16} /> },
  { label: 'Show Steps', prompt: 'Show me step by step how to use this feature.', icon: <BookOpen size={16} /> },
  { label: 'Contact Admin', prompt: 'How do I contact the admin?', icon: <Settings size={16} /> },
];

type Tab = 'chat' | 'admin' | 'analytics';
type AdminTab = 'faqs' | 'errors' | 'manuals';

export default function App() {
  const [page, setPage] = useState('Upload Page');
  const [guidedMode, setGuidedMode] = useState(false);
  const [input, setInput] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [adminTab, setAdminTab] = useState<AdminTab>('faqs');
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: 'assistant',
      text: 'Hello! I am your AI assistant. Ask me how to use the app, explain an error, or request step-by-step help.',
      sourceType: 'welcome',
    },
  ]);

  // FAQ State
  const [adminFaqs, setAdminFaqs] = useState<FaqRecord[]>([]);
  const [faqQuestion, setFaqQuestion] = useState('');
  const [faqAnswer, setFaqAnswer] = useState('');
  const [faqTags, setFaqTags] = useState('upload,help');
  const [faqPage, setFaqPage] = useState('Upload Page');
  const [editingFaqId, setEditingFaqId] = useState<number | null>(null);

  // Error State
  const [adminErrors, setAdminErrors] = useState<ErrorRecord[]>([]);
  const [errorKey, setErrorKey] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [errorFix, setErrorFix] = useState('');
  const [errorPage, setErrorPage] = useState('Upload Page');
  const [editingErrorId, setEditingErrorId] = useState<number | null>(null);

  // Manual State
  const [adminManuals, setAdminManuals] = useState<ManualRecord[]>([]);
  const [manualTitle, setManualTitle] = useState('');
  const [manualContent, setManualContent] = useState('');
  const [manualTags, setManualTags] = useState('tutorial');
  const [manualPage, setManualPage] = useState('Upload Page');
  const [editingManualId, setEditingManualId] = useState<number | null>(null);

  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const nextId = useMemo(() => messages.length + 1, [messages.length]);

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (activeTab === 'analytics') {
      void loadAnalytics();
    } else if (activeTab === 'admin') {
      void loadData();
    }
  }, [activeTab]);

  async function loadData() {
    try {
      const [faqs, errors, manuals] = await Promise.all([
        fetch('/api/admin/faqs').then(r => r.json()),
        fetch('/api/admin/errors').then(r => r.json()),
        fetch('/api/admin/manuals').then(r => r.json()),
      ]);
      setAdminFaqs(faqs || []);
      setAdminErrors(errors || []);
      setAdminManuals(manuals || []);
    } catch (err) {
      console.error('Error loading data:', err);
    }
  }

  async function loadAnalytics() {
    setAnalyticsLoading(true);
    try {
      const response = await fetch('/api/admin/analytics');
      const data = (await response.json()) as AnalyticsData;
      setAnalytics(data);
    } finally {
      setAnalyticsLoading(false);
    }
  }

  async function sendQuestion(question: string) {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = { id: nextId, role: 'user', text: trimmed };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, page, guided_mode: guidedMode }),
      });

      const data = (await response.json()) as SupportResponse;
      setMessages((current) => [
        ...current,
        {
          id: current.length + 2,
          role: 'assistant',
          text: data.answer,
          steps: data.steps,
          reference: data.reference,
          sourceType: data.source_type,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function addOrUpdateFaq(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!faqQuestion.trim() || !faqAnswer.trim()) return;

    const method = editingFaqId ? 'PUT' : 'POST';
    const url = editingFaqId ? `/api/admin/faqs/${editingFaqId}` : '/api/admin/faqs';

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: faqQuestion, answer: faqAnswer, tags: faqTags, page: faqPage }),
    });

    setFaqQuestion('');
    setFaqAnswer('');
    setFaqTags('upload,help');
    setFaqPage('Upload Page');
    setEditingFaqId(null);
    await loadData();
  }

  async function deleteFaq(id: number) {
    if (!confirm('Delete this FAQ?')) return;
    await fetch(`/api/admin/faqs/${id}`, { method: 'DELETE' });
    await loadData();
  }

  async function addOrUpdateError(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!errorKey.trim() || !errorMessage.trim() || !errorFix.trim()) return;

    const method = editingErrorId ? 'PUT' : 'POST';
    const url = editingErrorId ? `/api/admin/errors/${editingErrorId}` : '/api/admin/errors';

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error_key: errorKey, message: errorMessage, fix: errorFix, page: errorPage }),
    });

    setErrorKey('');
    setErrorMessage('');
    setErrorFix('');
    setErrorPage('Upload Page');
    setEditingErrorId(null);
    await loadData();
  }

  async function deleteError(id: number) {
    if (!confirm('Delete this error entry?')) return;
    await fetch(`/api/admin/errors/${id}`, { method: 'DELETE' });
    await loadData();
  }

  async function addOrUpdateManual(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!manualTitle.trim() || !manualContent.trim()) return;

    const method = editingManualId ? 'PUT' : 'POST';
    const url = editingManualId ? `/api/admin/manuals/${editingManualId}` : '/api/admin/manuals';

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: manualTitle, content: manualContent, tags: manualTags, page: manualPage }),
    });

    setManualTitle('');
    setManualContent('');
    setManualTags('tutorial');
    setManualPage('Upload Page');
    setEditingManualId(null);
    await loadData();
  }

  async function deleteManual(id: number) {
    if (!confirm('Delete this manual?')) return;
    await fetch(`/api/admin/manuals/${id}`, { method: 'DELETE' });
    await loadData();
  }

  function startEditFaq(faq: FaqRecord) {
    setFaqQuestion(faq.question);
    setFaqAnswer(faq.answer);
    setFaqTags(faq.tags);
    setFaqPage(faq.page);
    setEditingFaqId(faq.id);
  }

  function startEditError(error: ErrorRecord) {
    setErrorKey(error.error_key);
    setErrorMessage(error.message);
    setErrorFix(error.fix);
    setErrorPage(error.page);
    setEditingErrorId(error.id);
  }

  function startEditManual(manual: ManualRecord) {
    setManualTitle(manual.title);
    setManualContent(manual.content);
    setManualTags(manual.tags);
    setManualPage(manual.page);
    setEditingManualId(manual.id);
  }

  function clearChat() {
    setMessages([
      {
        id: 1,
        role: 'assistant',
        text: 'Chat cleared. How can I help you?',
        sourceType: 'welcome',
      },
    ]);
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendQuestion(input);
    }
  };

  const maxPageCount = analytics?.by_page[0]?.count ?? 1;

  return (
    <div className="shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div>
          <div className="badge">AI Offline Support</div>
          <h1>App Assistant</h1>
          <p>Local FAQs, AI-powered manuals, and error explanations tailored to your current page.</p>
        </div>

        <div className="panel">
          <label htmlFor="page">Current Context</label>
          <select id="page" value={page} onChange={(e) => setPage(e.target.value)}>
            {pageOptions.map((o) => <option key={o}>{o}</option>)}
          </select>

          <label className="toggle">
            <input
              type="checkbox"
              checked={guidedMode}
              onChange={(e) => setGuidedMode(e.target.checked)}
            />
            <span>Guided Step-by-Step Mode</span>
          </label>
        </div>

        <div className="quick-actions">
          {quickPrompts.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => { setActiveTab('chat'); void sendQuestion(p.prompt); }}
            >
              {p.icon} {p.label}
            </button>
          ))}
        </div>

        {/* Tab nav */}
        <nav className="tab-nav">
          <button
            type="button"
            className={activeTab === 'chat' ? 'tab-btn active' : 'tab-btn'}
            onClick={() => setActiveTab('chat')}
          >
            <Bot size={15} /> Chat
          </button>
          <button
            type="button"
            className={activeTab === 'admin' ? 'tab-btn active' : 'tab-btn'}
            onClick={() => setActiveTab('admin')}
          >
            <Settings size={15} /> Admin
          </button>
          <button
            type="button"
            className={activeTab === 'analytics' ? 'tab-btn active' : 'tab-btn'}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart2 size={15} /> Analytics
          </button>
        </nav>
      </aside>

      {/* ── Main area ── */}
      <main className="main">

        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <section className="chat-card">
            <div className="chat-header">
              <div>
                <h2>Support Chat</h2>
                <p>Ask a question or report an issue. I'm aware of your current page context.</p>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div className="status">Context: {page}</div>
                <button
                  type="button"
                  title="Clear chat"
                  onClick={clearChat}
                  style={{ padding: '0.5rem', borderRadius: '10px', background: 'rgba(255,75,75,0.15)', boxShadow: 'none', color: '#ff6b6b' }}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>

            <div className="messages">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-header">
                    {message.role === 'assistant' ? (
                      <>
                        <div className="avatar"><Bot size={14} /></div>
                        <span>AI Assistant</span>
                        {message.sourceType && message.sourceType !== 'welcome' && (
                          <span className="source-badge">{message.sourceType.replace('ai_', '✦ ')}</span>
                        )}
                      </>
                    ) : (
                      <>
                        <span>You</span>
                        <div className="avatar"><User size={14} /></div>
                      </>
                    )}
                  </div>
                  <div className="bubble">
                    <p>{message.text}</p>
                    {message.steps && message.steps.length > 0 && (
                      <ol>
                        {message.steps.map((step) => <li key={step}>{step}</li>)}
                      </ol>
                    )}
                    {(message.reference || message.sourceType) && (
                      <div className="metadata">
                        {message.reference && <span><BookOpen size={12} /> {message.reference}</span>}
                        {message.sourceType && <span><CheckCircle size={12} /> {message.sourceType}</span>}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              {loading && (
                <article className="message assistant">
                  <div className="message-header">
                    <div className="avatar"><Bot size={14} /></div>
                    <span>AI Assistant</span>
                  </div>
                  <div className="bubble">
                    <div className="typing-indicator">
                      <span /><span /><span />
                    </div>
                  </div>
                </article>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form
              className="composer"
              onSubmit={(e) => { e.preventDefault(); void sendQuestion(input); }}
            >
              <textarea
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a question… (Shift+Enter for new line)"
              />
              <div className="composer-row">
                <button type="submit" disabled={loading || !input.trim()}>
                  <Send size={16} /> {loading ? 'Thinking…' : 'Send Message'}
                </button>
              </div>
            </form>
          </section>
        )}

        {/* ADMIN TAB */}
        {activeTab === 'admin' && (
          <section className="admin-card">
            <div className="admin-tab-nav">
              <button
                className={adminTab === 'faqs' ? 'admin-tab-btn active' : 'admin-tab-btn'}
                onClick={() => setAdminTab('faqs')}
              >
                <BookOpen size={14} /> FAQs ({adminFaqs.length})
              </button>
              <button
                className={adminTab === 'errors' ? 'admin-tab-btn active' : 'admin-tab-btn'}
                onClick={() => setAdminTab('errors')}
              >
                <AlertCircle size={14} /> Errors ({adminErrors.length})
              </button>
              <button
                className={adminTab === 'manuals' ? 'admin-tab-btn active' : 'admin-tab-btn'}
                onClick={() => setAdminTab('manuals')}
              >
                <BookOpen size={14} /> Manuals ({adminManuals.length})
              </button>
            </div>

            {/* FAQs Tab */}
            {adminTab === 'faqs' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Manage FAQs</h2>
                <form className="admin-form" onSubmit={(e) => void addOrUpdateFaq(e)}>
                  <input
                    value={faqQuestion}
                    onChange={(e) => setFaqQuestion(e.target.value)}
                    placeholder="Question (e.g. How do I…)"
                    required
                  />
                  <textarea
                    rows={3}
                    value={faqAnswer}
                    onChange={(e) => setFaqAnswer(e.target.value)}
                    placeholder="Answer content…"
                    required
                  />
                  <div className="row">
                    <input
                      value={faqTags}
                      onChange={(e) => setFaqTags(e.target.value)}
                      placeholder="Tags (comma separated)"
                    />
                    <select value={faqPage} onChange={(e) => setFaqPage(e.target.value)}>
                      {pageOptions.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  </div>
                  <div className="button-group">
                    <button type="submit"><CheckCircle size={16} /> {editingFaqId ? 'Update' : 'Add'} FAQ</button>
                    {editingFaqId && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingFaqId(null);
                          setFaqQuestion('');
                          setFaqAnswer('');
                          setFaqTags('upload,help');
                          setFaqPage('Upload Page');
                        }}
                        style={{ background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                      >
                        <X size={16} /> Cancel
                      </button>
                    )}
                  </div>
                </form>

                <div className="faq-list">
                  {adminFaqs.map((faq) => (
                    <article key={faq.id} className="faq-item">
                      <strong>{faq.question}</strong>
                      <p>{faq.answer}</p>
                      <div className="meta">
                        <span>{faq.page}</span>
                        <span>{faq.tags}</span>
                      </div>
                      <div className="item-actions">
                        <button
                          type="button"
                          onClick={() => startEditFaq(faq)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px' }}
                        >
                          <Edit2 size={12} /> Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteFaq(faq.id)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px', background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {/* Errors Tab */}
            {adminTab === 'errors' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Manage Error Responses</h2>
                <form className="admin-form" onSubmit={(e) => void addOrUpdateError(e)}>
                  <input
                    value={errorKey}
                    onChange={(e) => setErrorKey(e.target.value)}
                    placeholder="Error Key (e.g., UPLOAD_413)"
                    required
                  />
                  <input
                    value={errorMessage}
                    onChange={(e) => setErrorMessage(e.target.value)}
                    placeholder="Error Message"
                    required
                  />
                  <textarea
                    rows={3}
                    value={errorFix}
                    onChange={(e) => setErrorFix(e.target.value)}
                    placeholder="How to fix this error…"
                    required
                  />
                  <div className="row">
                    <select value={errorPage} onChange={(e) => setErrorPage(e.target.value)}>
                      {pageOptions.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  </div>
                  <div className="button-group">
                    <button type="submit"><CheckCircle size={16} /> {editingErrorId ? 'Update' : 'Add'} Error</button>
                    {editingErrorId && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingErrorId(null);
                          setErrorKey('');
                          setErrorMessage('');
                          setErrorFix('');
                          setErrorPage('Upload Page');
                        }}
                        style={{ background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                      >
                        <X size={16} /> Cancel
                      </button>
                    )}
                  </div>
                </form>

                <div className="faq-list">
                  {adminErrors.map((error) => (
                    <article key={error.id} className="faq-item">
                      <strong>{error.error_key}</strong>
                      <p><em>{error.message}</em></p>
                      <p>{error.fix}</p>
                      <div className="meta">
                        <span>{error.page}</span>
                      </div>
                      <div className="item-actions">
                        <button
                          type="button"
                          onClick={() => startEditError(error)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px' }}
                        >
                          <Edit2 size={12} /> Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteError(error.id)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px', background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {/* Manuals Tab */}
            {adminTab === 'manuals' && (
              <div>
                <h2 style={{ marginBottom: '1rem' }}>Manage Manuals</h2>
                <form className="admin-form" onSubmit={(e) => void addOrUpdateManual(e)}>
                  <input
                    value={manualTitle}
                    onChange={(e) => setManualTitle(e.target.value)}
                    placeholder="Manual Title"
                    required
                  />
                  <textarea
                    rows={4}
                    value={manualContent}
                    onChange={(e) => setManualContent(e.target.value)}
                    placeholder="Manual Content…"
                    required
                  />
                  <div className="row">
                    <input
                      value={manualTags}
                      onChange={(e) => setManualTags(e.target.value)}
                      placeholder="Tags (comma separated)"
                    />
                    <select value={manualPage} onChange={(e) => setManualPage(e.target.value)}>
                      {pageOptions.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  </div>
                  <div className="button-group">
                    <button type="submit"><CheckCircle size={16} /> {editingManualId ? 'Update' : 'Add'} Manual</button>
                    {editingManualId && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingManualId(null);
                          setManualTitle('');
                          setManualContent('');
                          setManualTags('tutorial');
                          setManualPage('Upload Page');
                        }}
                        style={{ background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                      >
                        <X size={16} /> Cancel
                      </button>
                    )}
                  </div>
                </form>

                <div className="faq-list">
                  {adminManuals.map((manual) => (
                    <article key={manual.id} className="faq-item">
                      <strong>{manual.title}</strong>
                      <p>{manual.content}</p>
                      <div className="meta">
                        <span>{manual.page}</span>
                        <span>{manual.tags}</span>
                      </div>
                      <div className="item-actions">
                        <button
                          type="button"
                          onClick={() => startEditManual(manual)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px' }}
                        >
                          <Edit2 size={12} /> Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteManual(manual.id)}
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '4px', background: 'rgba(255,75,75,0.15)', color: '#ff6b6b' }}
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* ANALYTICS TAB */}
        {activeTab === 'analytics' && (
          <section className="admin-card">
            <div className="chat-header compact">
              <div>
                <h2>Usage Analytics</h2>
                <p>Track the most common questions and page activity.</p>
              </div>
              <button
                type="button"
                onClick={() => void loadAnalytics()}
                style={{ padding: '0.5rem 1rem', borderRadius: '12px', fontSize: '0.85rem' }}
              >
                Refresh
              </button>
            </div>

            {analyticsLoading && <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '2rem' }}>Loading analytics…</p>}

            {analytics && !analyticsLoading && (
              <>
                <div className="analytics-stat-row">
                  <div className="stat-card">
                    <span className="stat-number">{analytics.total_questions}</span>
                    <span className="stat-label">Total Questions Asked</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-number">{analytics.top_questions.length}</span>
                    <span className="stat-label">Unique Questions</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-number">{analytics.by_page.length}</span>
                    <span className="stat-label">Active Pages</span>
                  </div>
                </div>

                <div className="analytics-grid">
                  <div className="analytics-panel">
                    <h3>Top Questions</h3>
                    {analytics.top_questions.length === 0 && (
                      <p style={{ color: 'var(--muted)', padding: '1rem 0' }}>No data yet — start chatting!</p>
                    )}
                    {analytics.top_questions.map((q, i) => (
                      <div key={i} className="analytics-row">
                        <span className="analytics-rank">#{i + 1}</span>
                        <span className="analytics-question">{q.question}</span>
                        <span className="analytics-count">{q.count}×</span>
                      </div>
                    ))}
                  </div>

                  <div className="analytics-panel">
                    <h3>Questions by Page</h3>
                    {analytics.by_page.length === 0 && (
                      <p style={{ color: 'var(--muted)', padding: '1rem 0' }}>No data yet.</p>
                    )}
                    {analytics.by_page.map((p, i) => (
                      <div key={i} className="analytics-bar-row">
                        <span className="analytics-page-name">{p.page}</span>
                        <div className="analytics-bar-track">
                          <div
                            className="analytics-bar-fill"
                            style={{ width: `${Math.round((p.count / maxPageCount) * 100)}%` }}
                          />
                        </div>
                        <span className="analytics-count">{p.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
