const API_BASE = window.location.origin;
let jwtToken = null;
let currentOperatorId = null;
let currentMode = 'ROVER'; // 'ROVER' or 'UAV'

// UI Elements: Authentication & Flow
const landingPage = document.getElementById('landingPage');
const triggerAuthBtn = document.getElementById('triggerAuthBtn');
const authOverlay = document.getElementById('authOverlay');
const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const operatorIdInput = document.getElementById('operatorIdInput');
const verifyIdBtn = document.getElementById('verifyIdBtn');
const step1Status = document.getElementById('step1Status');
const authStatus = document.getElementById('authStatus');

const appWrapper = document.getElementById('appWrapper');
const opLabel = document.getElementById('opLabel');

// Camera & Biometrics
const webcamFeed = document.getElementById('webcamFeed');
const captureCanvas = document.getElementById('captureCanvas');

// Dashboard Panels
const modeRoverBtn = document.getElementById('modeRoverBtn');
const modeUavBtn = document.getElementById('modeUavBtn');
const robotObj = document.getElementById('robotObj');
const altContainer = document.getElementById('altContainer');
const altFill = document.getElementById('altFill');
const altValue = document.getElementById('altValue');
const mapView = document.getElementById('mapView');

// Tabs
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

// Role Selection Flow
const roleSelection = document.getElementById('roleSelection');
const roleAdminBtn = document.getElementById('roleAdminBtn');
const roleOperatorBtn = document.getElementById('roleOperatorBtn');

const adminLogin = document.getElementById('adminLogin');
const adminUserInput = document.getElementById('adminUserInput');
const adminPassInput = document.getElementById('adminPassInput');
const adminAuthBtn = document.getElementById('adminAuthBtn');
const adminLoginStatus = document.getElementById('adminLoginStatus');
const adminAppWrapper = document.getElementById('adminAppWrapper');
const adminTable = document.getElementById('adminTable');

const forgotPasswordLink = document.getElementById('forgotPasswordLink');
const forgotPasswordPanel = document.getElementById('forgotPasswordPanel');
const newAdminPassInput = document.getElementById('newAdminPassInput');
const resetPasswordBtn = document.getElementById('resetPasswordBtn');
const resetPasswordStatus = document.getElementById('resetPasswordStatus');

const adminBackBtn = document.getElementById('adminBackBtn');
const forgotBackBtn = document.getElementById('forgotBackBtn');
const opStep1BackBtn = document.getElementById('opStep1BackBtn');
const opStep2BackBtn = document.getElementById('opStep2BackBtn');

const adminResetIsolationBtn = document.getElementById('adminResetIsolationBtn');
const isolationBanner = document.getElementById('isolationBanner');
const executeCommandBtn = document.getElementById('executeCommandBtn');

let operatorPolling = null;
let movementChart = null;
let movementDataX = [];
let movementDataY = [];
let movementDataZ = []; // Added Z vector Tracker
let movementDataText = [];
let currentPosVector = {x: null, y: null, z: null};

// Toggles & Tabs
triggerAuthBtn.addEventListener('click', () => {
    landingPage.style.display = 'none';
    authOverlay.style.display = 'flex';
    roleSelection.style.display = 'block';
    step1.style.display = 'none';
});

roleOperatorBtn.addEventListener('click', () => {
    roleSelection.style.display = 'none';
    step1.style.display = 'block';
});

roleAdminBtn.addEventListener('click', () => {
    roleSelection.style.display = 'none';
    adminLogin.style.display = 'block';
});

adminBackBtn.addEventListener('click', () => {
    adminLogin.style.display = 'none';
    adminUserInput.value = '';
    adminPassInput.value = '';
    adminLoginStatus.textContent = '';
    roleSelection.style.display = 'block';
});

forgotPasswordLink.addEventListener('click', (e) => {
    e.preventDefault();
    adminLogin.style.display = 'none';
    forgotPasswordPanel.style.display = 'block';
});

forgotBackBtn.addEventListener('click', () => {
    forgotPasswordPanel.style.display = 'none';
    newAdminPassInput.value = '';
    resetPasswordStatus.textContent = '';
    adminLogin.style.display = 'block';
});

resetPasswordBtn.addEventListener('click', async () => {
    const newPass = newAdminPassInput.value.trim();
    if (!newPass) return;
    try {
        const r = await fetch(`${API_BASE}/api/admin/change-password`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ new_password: newPass })
        });
        if (!r.ok) throw new Error("Failed to reset passphrase.");
        resetPasswordStatus.textContent = "Passphrase successfully updated.";
        resetPasswordStatus.style.color = "var(--success-glow)";
        setTimeout(() => { forgotBackBtn.click(); }, 1500);
    } catch (e) {
        resetPasswordStatus.textContent = e.message;
        resetPasswordStatus.style.color = "var(--danger-glow)";
    }
});

opStep1BackBtn.addEventListener('click', () => {
    step1.style.display = 'none';
    operatorIdInput.value = '';
    step1Status.textContent = '';
    roleSelection.style.display = 'block';
});

opStep2BackBtn.addEventListener('click', () => {
    step2.style.display = 'none';
    if(webcamFeed.srcObject) {
        webcamFeed.srcObject.getTracks().forEach(t => t.stop());
    }
    step1.style.display = 'block';
});

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.target).classList.add('active');
    });
});

function toggleRobotMode(mode) {
    currentMode = mode;
    if (mode === 'ROVER') {
        modeRoverBtn.style.background = 'rgba(56, 189, 248, 0.1)';
        modeRoverBtn.style.color = 'var(--accent-glow)';
        modeRoverBtn.style.borderColor = 'rgba(56, 189, 248, 0.3)';
        
        modeUavBtn.style.background = 'transparent';
        modeUavBtn.style.color = 'var(--text-secondary)';
        modeUavBtn.style.borderColor = 'var(--text-secondary)';
        
        mapView.classList.remove('drone-mode');
        altContainer.style.opacity = '0.3';
    } else {
        modeUavBtn.style.background = 'rgba(16, 185, 129, 0.1)';
        modeUavBtn.style.color = 'var(--success-glow)';
        modeUavBtn.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        
        modeRoverBtn.style.background = 'transparent';
        modeRoverBtn.style.color = 'var(--text-secondary)';
        modeRoverBtn.style.borderColor = 'var(--text-secondary)';
        
        mapView.classList.add('drone-mode');
        altContainer.style.opacity = '1';
    }
}

// Set mode toggle listeners
modeRoverBtn.addEventListener('click', async () => {
    if(!jwtToken) return;
    try {
        await fetch(`${API_BASE}/api/robot/config`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${jwtToken}`},
            body: JSON.stringify({ mode: 'ROVER' })
        });
        toggleRobotMode('ROVER');
    }catch(e){}
});

modeUavBtn.addEventListener('click', async () => {
    if(!jwtToken) return;
    try {
        await fetch(`${API_BASE}/api/robot/config`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${jwtToken}`},
            body: JSON.stringify({ mode: 'UAV' })
        });
        toggleRobotMode('UAV');
    }catch(e){}
});

// ================================
// MFA logic
// ================================

verifyIdBtn.addEventListener('click', async () => {
    const opId = operatorIdInput.value.trim();
    if (!opId) return;
    verifyIdBtn.disabled = true;
    step1Status.textContent = 'Verifying ID metrics...';
    try {
        const r = await fetch(`${API_BASE}/api/auth/validate_id`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ operator_id: opId })
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail);
        
        currentOperatorId = opId;
        step1.style.display = 'none';
        step2.style.display = 'block';
        initWebcam();
    } catch(e) {
        step1Status.textContent = e.message;
        step1Status.style.color = 'var(--danger-glow)';
    } finally {
        verifyIdBtn.disabled = false;
    }
});

async function initWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        webcamFeed.srcObject = stream;
    } catch (err) {
        authStatus.textContent = "Camera hardware offline/blocked.";
        authStatus.style.color = "var(--danger-glow)";
    }
}

function captureFrame() {
    const ctx = captureCanvas.getContext('2d');
    ctx.drawImage(webcamFeed, 0, 0, captureCanvas.width, captureCanvas.height);
    return captureCanvas.toDataURL('image/jpeg', 0.8);
}

document.getElementById('registerFaceBtn').addEventListener('click', async () => {
    authStatus.textContent = 'Curating biometric mesh... Keep still.';
    authStatus.style.color = "white";
    const frames = [];
    for(let i=0; i<5; i++){
        frames.push(captureFrame());
        await new Promise(r => setTimeout(r, 200));
    }
    try {
        const r = await fetch(`${API_BASE}/api/auth/register_face`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ images: frames, operator_id: currentOperatorId })
        });
        const data = await r.json();
        if(!r.ok) throw new Error(data.detail);
        authStatus.textContent = "Imprint Stored. Awaiting Login auth.";
        authStatus.style.color = "var(--success-glow)";
    } catch(e) {
        authStatus.textContent = e.message;
        authStatus.style.color = "var(--danger-glow)";
    }
});

document.getElementById('loginFaceBtn').addEventListener('click', async () => {
    authStatus.textContent = 'Solving biometric hash...';
    authStatus.style.color = "white";
    const frame = captureFrame();
    try {
        const r = await fetch(`${API_BASE}/api/auth/login_face`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: frame, operator_id: currentOperatorId })
        });
        const data = await r.json();
        if(!r.ok) throw new Error(data.detail || "Authentication denied by Neural Core.");
        
        jwtToken = data.access_token;
        authStatus.textContent = "Granted.";
        authStatus.style.color = "var(--success-glow)";
        
        setTimeout(() => {
            if(webcamFeed.srcObject) {
                webcamFeed.srcObject.getTracks().forEach(t => t.stop());
            }
            authOverlay.style.opacity = '0';
            setTimeout(() => {
                authOverlay.style.display = 'none';
                appWrapper.style.display = 'block';
                opLabel.textContent = currentOperatorId;
                fetchRobotState(); // pull initial data
                operatorPolling = setInterval(fetchRobotState, 2000); // Live hardware tracking
            }, 500);
        }, 800);
        
    } catch(e) {
        authStatus.textContent = e.message;
        authStatus.style.color = "var(--danger-glow)";
    }
});

// ================================
// Robot Simulation & Features
// ================================

function updateVisualRobot(state) {
    if(!state) return;
    const pxScale = 10;
    
    // Map View
    robotObj.style.left = `calc(50% + ${state.x * pxScale}px)`;
    robotObj.style.top = `calc(50% - ${state.y * pxScale}px)`;
    if(state.mode === 'ROVER') {
        robotObj.style.transform = `rotate(${-state.heading_deg}deg)`;
    } else {
        // Keep drone crosshair unrotated, just move it.
        robotObj.style.transform = `rotate(0deg)`;
    }

    // Altimeter view
    if(state.mode === 'UAV') {
        // Max altitude visual limit ~200m
        const altPct = Math.min(100, Math.max(0, (state.z / 200) * 100));
        altFill.style.height = `${altPct}%`;
        altValue.textContent = `${state.z}m`;
        if (state.z > 0) {
            robotObj.style.transform = `scale(${1 + state.z/150})`;
        } else {
            robotObj.style.transform = `scale(1)`;
        }
    }
    
    // Sync UI Mode to backed
    if (state.mode && state.mode !== currentMode) {
        toggleRobotMode(state.mode);
    }
    updateChartVector(state);
}

function updateChartVector(state) {
    if (!movementChart) {
        movementChart = true; // Flag that it is initialized
        const layout = {
            margin: { l: 0, r: 0, b: 0, t: 0 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            scene: {
                xaxis: { title: 'X (Lon)', color: '#94A3B8', gridcolor: 'rgba(255,255,255,0.1)' },
                yaxis: { title: 'Y (Lat)', color: '#94A3B8', gridcolor: 'rgba(255,255,255,0.1)' },
                zaxis: { title: 'Z (Alt)', color: '#94A3B8', gridcolor: 'rgba(255,255,255,0.1)' }
            }
        };
        Plotly.newPlot('movementChart3D', [{
            type: 'scatter3d', mode: 'lines+markers',
            x: movementDataX, y: movementDataY, z: movementDataZ,
            text: movementDataText,
            hoverinfo: 'text+x+y+z',
            line: { width: 4, color: '#38BDF8' },
            marker: { size: 3, color: '#10B981' }
        }], layout, {responsive: true});
    }

    const posStr = `[X: ${state.x.toFixed(1)}, Y: ${state.y.toFixed(1)}, Z: ${state.mode==='UAV'?state.z.toFixed(1):0}, θ: ${state.heading_deg}°]`;
    document.getElementById('positionVectorDisplay').textContent = posStr;
    
    if (currentPosVector.x !== state.x || currentPosVector.y !== state.y || currentPosVector.z !== state.z) {
        currentPosVector.x = state.x;
        currentPosVector.y = state.y;
        currentPosVector.z = state.z;

        movementDataX.push(state.x);
        movementDataY.push(state.y);
        movementDataZ.push(state.mode === 'UAV' ? state.z : 0);
        movementDataText.push(state.last_command || "IDLE");
        
        if (movementDataX.length > 30) {
            movementDataX.shift();
            movementDataY.shift();
            movementDataZ.shift();
            movementDataText.shift();
        }
        
        Plotly.update('movementChart3D', {
            x: [movementDataX], y: [movementDataY], z: [movementDataZ], text: [movementDataText]
        });
    }
}

async function fetchRobotState() {
    try {
        const url = currentOperatorId ? `${API_BASE}/api/robot/state?operator_id=${currentOperatorId}` : `${API_BASE}/api/robot/state`;
        const r = await fetch(url);
        const data = await r.json();
        
        if (r.status === 401 || r.status === 403) {
            // Operator Revoked!
            alert(`[CRITICAL] ${data.detail}`);
            document.getElementById('logoutBtn').click();
            return;
        }

        if(data && data.state) updateVisualRobot(data.state);
        
        if (data.allowed_commands) {
            document.getElementById('allowedCommandsDisplay').textContent = data.allowed_commands.join(", ");
        }
        
        // Handle isolation state
        if (data.is_isolated !== undefined) {
            handleIsolationState(data.is_isolated);
        }
    } catch(e){}
}

function handleIsolationState(isIsolated) {
    if (isIsolated) {
        isolationBanner.style.display = 'block';
        executeCommandBtn.disabled = true;
        adminResetIsolationBtn.style.display = 'inline-block';
    } else {
        isolationBanner.style.display = 'none';
        executeCommandBtn.disabled = false;
        adminResetIsolationBtn.style.display = 'none';
    }
}

document.getElementById('executeCommandBtn').addEventListener('click', async () => {
    const cmdInput = document.getElementById('robotCommand');
    const sourceContextInput = document.getElementById('sourceContext');
    const result = document.getElementById('robotResult');
    const cmd = cmdInput.value.trim();
    const sourceContext = sourceContextInput.value.trim();
    
    if (!cmd) return;
    
    if (!sourceContext) {
        result.innerHTML = `<span style="color:var(--danger-glow);">[ERROR] Protocol Violation: Must provide origin instruction context for Phishing analysis.</span>`;
        return;
    }
    
    result.innerHTML = '<span style="color:var(--text-secondary);">Calculating RSA-PSS Hash...</span>';
    
    try {
        const signR = await fetch(`${API_BASE}/api/crypto/sign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: cmd })
        });
        const signData = await signR.json();
        if (!signR.ok) throw new Error("RSA Signature Rejected by Hardware Layer");

        const payload = {
            command: cmd,
            signature_b64: signData.signature_b64,
        };
        // Only attach if present
        if (sourceContext) {
            payload.source_context = sourceContext;
        }

        const execR = await fetch(`${API_BASE}/api/robot/command`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify(payload),
        });
        const execData = await execR.json();
        if (execData.success) {
            result.innerHTML = `<span style="color:var(--success-glow);">[SUCCESS]</span> Transmitted: ${execData.message} | Pos: [X:${execData.state.x}, Y:${execData.state.y}${execData.state.mode==='UAV' ? ', Z:'+execData.state.z : ''}]`;
            updateVisualRobot(execData.state);
        } else if (execData.code === 'PENDING_APPROVAL') {
            result.innerHTML = `<span style="color:#FBBF24;">[PENDING ADMIN APPROVAL]</span> Linguistic Model flagged execution. Waiting for Cryptographic Admin review...`;
            // Temporary poll to see if state catches up (if admin approved it)
            const checkLedgerId = setInterval(async () => {
                const trRes = await fetch(`${API_BASE}/api/admin/transactions`);
                const trData = await trRes.json();
                const tx = trData.transactions.find(t => t.id === execData.transaction_id);
                if(tx && tx.status === 'APPROVED') {
                    result.innerHTML = `<span style="color:var(--success-glow);">[APPROVED BY ADMIN]</span> Transmitted and executed via master override.`;
                    clearInterval(checkLedgerId);
                } else if (tx && tx.status === 'REJECTED') {
                    result.innerHTML = `<span style="color:var(--danger-glow);">[DENIED BY ADMIN]</span> Administrator explicitly rejected transaction.`;
                    clearInterval(checkLedgerId);
                }
            }, 2000);
        } else {
            // Check if it's a Phishing rejection specifically
            if (execData.code === 'SAFETY_VIOLATION') {
                result.innerHTML = `<span style="color:#ef4444; font-weight:bold;">[ASIMOV VIOLATION]</span> ${execData.message}. Network Isolation Triggered!`;
            } else if (execData.code === 'PHISHING_RISK') {
                result.innerHTML = `<span style="color:var(--danger-glow);">[AI INTERCEPT]</span> Neural Net rejected origin text as phishing! (Score ${execData.phishing_score})`;
            } else {
                result.innerHTML = `<span style="color:var(--danger-glow);">[REJECTED]</span> ${execData.message || execData.code}`;
            }
        }
    } catch (e) {
        result.innerHTML = `<span style="color:var(--danger-glow);">[FATAL]</span> ${e.message}`;
    }
});

document.getElementById('checkPhishingBtn').addEventListener('click', async () => {
    const input = document.getElementById('phishingInput').value.trim();
    const res = document.getElementById('phishingResult');
    if (!input) return;
    res.textContent = 'Aggregating vector via Support Vector / TF-IDF models...';
    try {
        const r = await fetch(`${API_BASE}/api/phishing/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: input })
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail);
        
        let output = "";
        if (!data.is_safe) {
            output += `<div style="color:#ef4444; font-weight:bold; margin-bottom:10px;">[!] ASIMOV SAFETY FAILURE: ${data.safety_reason}</div>`;
        } else {
            output += `<div style="color:var(--success-glow); margin-bottom:10px;">[+] ASIMOV SAFETY: Passed. No kinetic threats detected.</div>`;
        }
        
        output += data.is_phishing ? 
            `<div style="color:var(--danger-glow);">[-] PHISHING ENGINE: MALICIOUS AI INTERCEPT DETECTED (${(data.score*100).toFixed(1)}% certainty)</div>` 
            : `<div style="color:var(--success-glow);">[+] PHISHING ENGINE: CLEAN. Safe for network transmission.</div>`;
            
        res.innerHTML = output;
    } catch (e) {
        res.textContent = e.message;
    }
});

// Admin Flow & Polling
adminAuthBtn.addEventListener('click', async () => {
    const user = adminUserInput.value.trim();
    const pass = adminPassInput.value.trim();
    if (!user || !pass) return;
    adminAuthBtn.disabled = true;
    adminLoginStatus.textContent = 'Verifying Base Hash...';
    try {
        const r = await fetch(`${API_BASE}/api/admin/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: user, password: pass })
        });
        if (!r.ok) throw new Error("Invalid cryptographic seal.");
        
        // Success
        authOverlay.style.display = 'none';
        adminAppWrapper.style.display = 'block';
        fetchAdminTransactions();
        fetchAdminOperators();
        adminPolling = setInterval(() => { fetchAdminTransactions(); fetchAdminOperators(); }, 3000);
        setInterval(fetchRobotState, 3000); // Admins also follow robot updates
    } catch (e) {
        adminLoginStatus.textContent = e.message;
    } finally {
        adminAuthBtn.disabled = false;
    }
});

async function fetchAdminTransactions() {
    try {
        const r = await fetch(`${API_BASE}/api/admin/transactions`);
        const data = await r.json();
        renderAdminTable(data.transactions);
    } catch(e) {}
}

async function fetchAdminOperators() {
    try {
        const r = await fetch(`${API_BASE}/api/admin/operators`);
        const data = await r.json();
        renderUsersTable(data.operators);
    } catch(e) {}
}

function renderUsersTable(ops) {
    const tbody = document.querySelector('#usersTable tbody');
    tbody.innerHTML = '';
    ops.forEach(op => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${op.operator_id}</td>
            <td>${new Date(op.registered_at).toLocaleString()}</td>
            <td style="font-family:monospace; color:var(--success-glow);">${op.face_hash}</td>
            <td><button class="btn-primary" style="padding:0.4rem; padding-right:0.6rem; border-color:var(--danger-glow); color:var(--danger-glow);" onclick="revokeOperator('${op.operator_id}')">Revoke</button></td>
        `;
        tbody.appendChild(tr);
    });
}

window.revokeOperator = async (id) => {
    if(!confirm(`Revoke operator ${id}? This deletes their biometric profile and revokes dashboard access.`)) return;
    await fetch(`${API_BASE}/api/admin/operators/${id}`, {method: 'DELETE'});
    fetchAdminOperators();
};

function renderAdminTable(txs) {
    const tbody = adminTable.querySelector('tbody');
    tbody.innerHTML = '';
    txs.forEach(tx => {
        const tr = document.createElement('tr');
        
        let actions = '-';
        if (tx.status === 'PENDING') {
            actions = `<button class="btn-secondary" style="font-size:0.7rem; padding:0.4rem; padding-right:0.6rem; margin-right:5px;" onclick="approveTx('${tx.id}')">Approve</button>
                       <button class="btn-primary" style="font-size:0.7rem; padding:0.4rem; padding-right:0.6rem; border-color:var(--danger-glow); color:var(--danger-glow);" onclick="rejectTx('${tx.id}')">Deny</button>`;
        }
        
        let sClass = 'status-pending';
        if(tx.status === 'APPROVED') sClass = 'status-approved';
        if(tx.status === 'REJECTED') sClass = 'status-rejected';

        tr.innerHTML = `
            <td>
                <div class="tooltip-container">[${tx.id.substring(0,8)}]
                    <span class="tooltip-text">
                        <strong>Cryptographic Verification:</strong><br/>
                        Method: ${tx.crypto_technique}<br/>
                        Signature Block:<br/>
                        ${tx.crypto_hash}<br/>
                        <br/>
                        <em>Provable non-repudiation enforced via mathematical identity match.</em>
                    </span>
                </div>
            </td>
            <td style="font-family:monospace;">${tx.operator_id}</td>
            <td style="font-family:monospace; color:var(--text-secondary);">${tx.command}</td>
            <td style="font-family:monospace; color:${tx.phishing_score >= 0.7 ? 'var(--danger-glow)' : (tx.phishing_score >= 0.3 ? '#FBBF24' : 'var(--success-glow)')};">${tx.phishing_score}</td>
            <td class="${sClass}">${tx.status}</td>
            <td>${actions}</td>
        `;
        tbody.appendChild(tr);
    });
}

window.approveTx = async (id) => {
    if(!confirm("Authorize execution on live hardware?")) return;
    await fetch(`${API_BASE}/api/admin/transactions/${id}/approve`, {method: 'POST'});
    fetchAdminTransactions();
}
window.rejectTx = async (id) => {
    await fetch(`${API_BASE}/api/admin/transactions/${id}/reject`, {method: 'POST'});
    fetchAdminTransactions();
}

adminResetIsolationBtn.addEventListener('click', async () => {
    if(!confirm("Are you sure you want to disengage Network Isolation? This will restore hardware uplink to operator terminals.")) return;
    try {
        await fetch(`${API_BASE}/api/admin/isolation/reset`, {method: 'POST'});
        fetchAdminTransactions();
        fetchRobotState();
    } catch(e) {}
});

document.getElementById('adminRefreshBtn').addEventListener('click', async (e) => { 
    e.target.textContent = 'Refreshing...';
    await fetchAdminTransactions(); 
    await fetchAdminOperators(); 
    await fetchRobotState();
    setTimeout(() => { e.target.textContent = 'Refresh Uplinks'; }, 500);
});
document.getElementById('adminLogoutBtn').addEventListener('click', () => {
    clearInterval(adminPolling);
    adminAppWrapper.style.display = 'none';
    landingPage.style.display = 'flex';
    adminUserInput.value = '';
    adminPassInput.value = '';
    adminLoginStatus.textContent = '';
    adminLogin.style.display = 'none';
    roleSelection.style.display = 'block';
});

// Logout flow (Operator)
document.getElementById('logoutBtn').addEventListener('click', () => {
    clearInterval(operatorPolling);
    jwtToken = null;
    currentOperatorId = null;
    
    // Reset UI
    appWrapper.style.display = 'none';
    landingPage.style.display = 'flex';
    authOverlay.style.display = 'none';
    roleSelection.style.display = 'block';
    step1.style.display = 'none';
    step2.style.display = 'none';
    operatorIdInput.value = '';
    step1Status.textContent = '';
    authStatus.textContent = 'Awaiting biometric grid...';
    document.getElementById('robotResult').textContent = 'Awaiting command vector...';
    document.getElementById('allowedCommandsDisplay').textContent = 'Fetching commands...';
    document.getElementById('phishingResult').textContent = 'Awaiting injection...';
    document.getElementById('phishingInput').value = '';
    document.getElementById('robotCommand').value = '';
    
    // Plotly memory clear
    movementDataX = [];
    movementDataY = [];
    movementDataZ = [];
    movementDataText = [];
    if(movementChart) {
        Plotly.purge('movementChart3D');
        movementChart = null;
    }
    
    // Hard reset the simulator visually
    const pxScale = 10;
    robotObj.style.left = `50%`;
    robotObj.style.top = `50%`;
    robotObj.style.transform = `rotate(0deg) scale(1)`;
    altFill.style.height = `0%`;
    altValue.textContent = `0m`;
});
