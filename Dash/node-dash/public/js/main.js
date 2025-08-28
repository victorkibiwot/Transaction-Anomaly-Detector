document.getElementById('transactForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = Object.fromEntries(new FormData(e.target).entries());
    const res = await fetch('/transact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });
    const data = await res.json();
    document.getElementById('result').innerText = JSON.stringify(data);
});

document.getElementById('predictForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = Object.fromEntries(new FormData(e.target).entries());
    const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });
    const data = await res.json();
    document.getElementById('result').innerText = JSON.stringify(data);
});
