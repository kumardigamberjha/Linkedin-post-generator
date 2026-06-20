import { useState } from 'react';

export default function Pricing({ token }) {
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

  function showModal(title, message, onConfirm = null) {
    setModal({ isOpen: true, title, message, onConfirm });
  }

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '₹0',
      features: ['Gemini 3.5 Flash & Nemotron Ultra Only', '5 posts per month', 'Basic Support'],
      buttonText: 'Get Free'
    },
    {
      id: 'basic',
      name: 'Starter',
      price: '₹199',
      features: ['Gemini 3.5 Flash & Nemotron Ultra Only', '28 posts per month', 'Trend Searching', 'Standard Support'],
      buttonText: 'Get Starter'
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '₹499',
      features: ['Multiple Models (Claude, ChatGPT, Gemini)', '50 posts per month', 'Trend Searching', 'Priority Support'],
      buttonText: 'Get Pro',
      highlight: true
    },
    {
      id: 'max',
      name: 'Max',
      price: '₹699',
      features: ['Multiple Models (Claude, ChatGPT, Gemini)', '100 posts per month', 'Trend Searching', '24/7 Priority Support'],
      buttonText: 'Get Max'
    }
  ];

  async function handleSubscribe(planId) {
    if (!token) {
      showModal("Authentication Required", "Please log in to purchase a subscription plan.");
      return;
    }
    
    setLoading(true);
    
    // Quick handle for Free tier downgrade
    if (planId === 'free') {
      try {
        const res = await fetch('/api/payments/create-checkout-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ plan_id: planId })
        });
        const data = await res.json();
        if (data.mock) {
          showModal("Plan Updated", "Your account has successfully been set to the Free plan.", () => {
            window.location.reload();
          });
        }
      } catch (e) {
        showModal("Update Failed", "Could not switch to the Free plan. Please try again.");
      } finally {
        setLoading(false);
      }
      return;
    }

    try {
      const res = await fetch('/api/payments/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ plan_id: planId })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to start checkout');
      
      if (data.mock) {
        showModal("Subscription Active", "Mock Mode: Your subscription is now fully active!", () => {
          window.location.reload();
        });
      } else {
        window.location.href = data.url;
      }
    } catch (err) {
      showModal("Subscription Failed", err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '40px auto', padding: '0 20px' }}>
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <h1 style={{ fontSize: '32px', marginBottom: '12px' }}>Choose Your Plan</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '16px' }}>Unlock the full power of AI for your LinkedIn presence.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        {plans.map(plan => (
          <div key={plan.id} style={{ 
            background: 'var(--surface)', 
            border: plan.highlight ? '2px solid var(--linkedin-blue)' : '1px solid var(--border)', 
            borderRadius: '12px', 
            padding: '32px',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            boxShadow: plan.highlight ? '0 8px 24px rgba(10, 102, 194, 0.15)' : 'var(--shadow)'
          }}>
            {plan.highlight && (
              <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: 'var(--linkedin-blue)', color: 'white', padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }}>
                MOST POPULAR
              </div>
            )}
            
            <h3 style={{ margin: '0 0 16px 0', fontSize: '20px' }}>{plan.name}</h3>
            <div style={{ fontSize: '36px', fontWeight: 700, marginBottom: '24px' }}>
              {plan.price}<span style={{ fontSize: '16px', color: 'var(--text-muted)', fontWeight: 400 }}>/mo</span>
            </div>
            
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px 0', flex: 1 }}>
              {plan.features.map((feature, i) => (
                <li key={i} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  {feature}
                </li>
              ))}
            </ul>
            
            <button 
              className={plan.highlight ? "btn btn-primary" : "btn btn-secondary"}
              onClick={() => handleSubscribe(plan.id)}
              disabled={loading}
              style={{ width: '100%', padding: '12px', fontSize: '16px' }}
            >
              {loading ? 'Processing...' : plan.buttonText}
            </button>
          </div>
        ))}
      </div>

      {modal.isOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            padding: '32px',
            borderRadius: '16px',
            maxWidth: '400px',
            width: '90%',
            textAlign: 'center',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'var(--linkedin-blue-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
              color: 'var(--linkedin-blue)'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            </div>
            <h3 style={{ marginTop: 0, marginBottom: '8px', fontSize: '20px', fontWeight: 'bold' }}>{modal.title}</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '15px', lineHeight: '1.5' }}>{modal.message}</p>
            <button 
              className="btn btn-primary" 
              onClick={() => {
                const cb = modal.onConfirm;
                setModal({ isOpen: false, title: '', message: '', onConfirm: null });
                if (cb) cb();
              }}
              style={{ width: '100%', padding: '12px', fontSize: '15px', fontWeight: 'bold' }}
            >
              Okay, Got It
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
