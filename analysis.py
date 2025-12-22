"""
System Analysis Module
======================

Provides frequency response analysis, step response, and stability analysis
for the greenhouse heating system.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from model import ModelParams


def get_transfer_function(params: ModelParams):
    """
    Get transfer function from model parameters.

    The system is: T1*T2*ÿ + (T1+T2)*ẏ + y = K*u

    Transfer function: H(s) = K / (T1*T2*s^2 + (T1+T2)*s + 1)

    With transport delay L: G(s) = H(s) * e^(-L*s)
    """
    T1 = params.T1
    T2 = params.T2
    K = params.K
    L = params.L

    # Second-order system
    num = [K]
    den = [T1 * T2, T1 + T2, 1]

    # Create transfer function
    sys_no_delay = signal.TransferFunction(num, den)

    return sys_no_delay, L


def plot_step_response(params: ModelParams, duration=600.0, figsize=(12, 8)):
    """
    Plot step response (transient response) of the system.
    """
    sys, L = get_transfer_function(params)

    # Time vector
    t = np.linspace(0, duration, 1000)

    # Step response
    t_out, y_out = signal.step(sys, T=t)

    # Account for delay (shift response)
    y_delayed = np.zeros_like(y_out)
    delay_samples = int(L / (t[1] - t[0]))
    if delay_samples < len(y_out):
        y_delayed[delay_samples:] = y_out[:-delay_samples]

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

    # Step response
    ax1.plot(t_out, y_out, 'b-', linewidth=2, label='Without delay')
    ax1.plot(t_out, y_delayed, 'r--', linewidth=2, label=f'With delay L={L}s')
    ax1.axhline(y=y_out[-1], color='g', linestyle=':', label=f'Steady state = {y_out[-1]:.2f}')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Output (Temperature C)', fontsize=12)
    ax1.set_title('Step Response (Transient Process / Перехідний процес)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)

    # Info text
    settling_time = t_out[np.where(np.abs(y_out - y_out[-1]) < 0.02 * y_out[-1])[0][0]] if len(np.where(np.abs(y_out - y_out[-1]) < 0.02 * y_out[-1])[0]) > 0 else duration
    overshoot = ((np.max(y_out) - y_out[-1]) / y_out[-1] * 100) if y_out[-1] != 0 else 0

    info_text = f'Settling time (2%): {settling_time:.1f}s\nOvershoot: {overshoot:.1f}%\nFinal value: {y_out[-1]:.2f}C'
    ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontsize=10)

    # Derivative (rate of change)
    dy_dt = np.gradient(y_out, t_out)
    ax2.plot(t_out, dy_dt, 'g-', linewidth=2)
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Rate of change (C/s)', fontsize=12)
    ax2.set_title('Temperature Change Rate', fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_bode(params: ModelParams, figsize=(12, 10)):
    """
    Plot Bode diagram (Amplitude and Phase frequency response).

    Amplitude-frequency characteristic (Амплітудно-частотна характеристика)
    Phase-frequency characteristic (Фазово-частотна характеристика)
    """
    sys, L = get_transfer_function(params)

    # Frequency range (rad/s)
    w = np.logspace(-4, 0, 500)

    # Frequency response
    w_out, H = signal.freqs(sys.num, sys.den, worN=w)

    # Add delay effect: multiply by e^(-j*w*L)
    H_delayed = H * np.exp(-1j * w_out * L)

    # Magnitude and phase
    magnitude_db = 20 * np.log10(np.abs(H_delayed))
    phase_deg = np.angle(H_delayed, deg=True)

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

    # Amplitude-frequency response
    ax1.semilogx(w_out, magnitude_db, 'b-', linewidth=2)
    ax1.set_xlabel('Frequency ω (rad/s)', fontsize=12)
    ax1.set_ylabel('Magnitude (dB)', fontsize=12)
    ax1.set_title('Amplitude-Frequency Characteristic\n(Амплітудно-частотна характеристика)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, which='both', alpha=0.3)
    ax1.axhline(0, color='r', linestyle='--', linewidth=1)

    # Add -3dB line (bandwidth)
    ax1.axhline(-3, color='g', linestyle=':', linewidth=1, label='-3dB bandwidth')
    ax1.legend()

    # Phase-frequency response
    ax2.semilogx(w_out, phase_deg, 'r-', linewidth=2)
    ax2.set_xlabel('Frequency ω (rad/s)', fontsize=12)
    ax2.set_ylabel('Phase (degrees)', fontsize=12)
    ax2.set_title('Phase-Frequency Characteristic\n(Фазово-частотна характеристика)',
                  fontsize=14, fontweight='bold')
    ax2.grid(True, which='both', alpha=0.3)
    ax2.axhline(-180, color='r', linestyle='--', linewidth=1, label='−180°')
    ax2.legend()

    # Add gain and phase margin info
    # Find gain margin (where phase = -180°)
    idx_180 = np.argmin(np.abs(phase_deg + 180))
    gm_db = -magnitude_db[idx_180]
    gm_freq = w_out[idx_180]

    # Find phase margin (where magnitude = 0 dB)
    idx_0db = np.argmin(np.abs(magnitude_db))
    pm_deg = 180 + phase_deg[idx_0db]
    pm_freq = w_out[idx_0db]

    info_text = f'Gain Margin: {gm_db:.1f} dB at ω={gm_freq:.4f} rad/s\n'
    info_text += f'Phase Margin: {pm_deg:.1f}° at ω={pm_freq:.4f} rad/s'

    if gm_db < 6:
        info_text += '\n[!] Warning: Low gain margin (unstable!)'
    if pm_deg < 30:
        info_text += '\n[!] Warning: Low phase margin (oscillations!)'

    ax2.text(0.02, 0.02, info_text, transform=ax2.transAxes,
             verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontsize=10)

    plt.tight_layout()
    return fig


def plot_nyquist(params: ModelParams, figsize=(10, 10)):
    """
    Plot Nyquist diagram for stability analysis.
    """
    sys, L = get_transfer_function(params)

    # Frequency range
    w = np.logspace(-4, 1, 500)

    # Frequency response
    w_out, H = signal.freqs(sys.num, sys.den, worN=w)
    H_delayed = H * np.exp(-1j * w_out * L)

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Nyquist plot
    ax.plot(H_delayed.real, H_delayed.imag, 'b-', linewidth=2, label='Nyquist curve')
    ax.plot(H_delayed.real, -H_delayed.imag, 'b--', linewidth=1, alpha=0.5)

    # Critical point (-1, 0)
    ax.plot(-1, 0, 'rx', markersize=15, markeredgewidth=3, label='Critical point (-1, 0)')
    ax.axhline(0, color='k', linewidth=0.5)
    ax.axvline(0, color='k', linewidth=0.5)

    # Unit circle
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), 'g:', linewidth=1, alpha=0.5, label='Unit circle')

    ax.set_xlabel('Real axis', fontsize=12)
    ax.set_ylabel('Imaginary axis', fontsize=12)
    ax.set_title('Nyquist Diagram', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.axis('equal')

    # Check stability
    encirclements = 0  # Simplified check
    if np.min(np.abs(H_delayed + 1)) < 0.5:
        stability_text = '[!] System may be UNSTABLE (close to -1 point)'
        color = 'red'
    else:
        stability_text = '[OK] System appears STABLE'
        color = 'green'

    ax.text(0.02, 0.98, stability_text, transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor=color, alpha=0.3),
            fontsize=12, fontweight='bold')

    plt.tight_layout()
    return fig


def analyze_stability(params: ModelParams):
    """
    Analyze system stability and print report.
    """
    print("=" * 70)
    print("SYSTEM STABILITY ANALYSIS")
    print("=" * 70)

    T1 = params.T1
    T2 = params.T2
    K = params.K
    L = params.L

    print(f"\nParameters:")
    print(f"  K  = {K}")
    print(f"  T1 = {T1} s")
    print(f"  T2 = {T2} s")
    print(f"  L  = {L} s")

    # Characteristic equation: T1*T2*s^2 + (T1+T2)*s + 1 = 0
    a = T1 * T2
    b = T1 + T2
    c = 1.0

    # Roots (poles)
    discriminant = b**2 - 4*a*c
    if discriminant >= 0:
        root1 = (-b + np.sqrt(discriminant)) / (2*a)
        root2 = (-b - np.sqrt(discriminant)) / (2*a)
        print(f"\nPoles (real):")
        print(f"  s1 = {root1:.6f}")
        print(f"  s2 = {root2:.6f}")

        if root1 < 0 and root2 < 0:
            print("  [OK] Both poles negative -> STABLE")
        else:
            print("  [X] Positive pole(s) -> UNSTABLE")
    else:
        real_part = -b / (2*a)
        imag_part = np.sqrt(-discriminant) / (2*a)
        print(f"\nPoles (complex conjugate):")
        print(f"  s = {real_part:.6f} +/- j{imag_part:.6f}")

        if real_part < 0:
            print("  [OK] Negative real part -> STABLE")
            print(f"  Natural frequency: wn = {np.sqrt(c/a):.6f} rad/s")
            print(f"  Damping ratio: zeta = {b/(2*np.sqrt(a*c)):.6f}")
        else:
            print("  [X] Positive real part -> UNSTABLE")

    # DC gain
    dc_gain = K / c
    print(f"\nDC Gain: {dc_gain:.2f}")
    print(f"  -> Step input of 1.0 -> Final output ~ {dc_gain:.2f}C")

    if dc_gain > 100:
        print("  [!] WARNING: Very high gain! Temperature will grow rapidly!")

    # Time constants
    print(f"\nTime constants:")
    print(f"  Dominant: T1 = {T1} s")
    print(f"  Secondary: T2 = {T2} s")
    print(f"  Approximate settling time: {4 * max(T1, T2):.1f} s")

    # Transport delay effect
    print(f"\nTransport delay: L = {L} s")
    if L > 0.2 * max(T1, T2):
        print("  [!] Significant delay (>20% of time constant) - may cause oscillations")

    print("\n" + "=" * 70)

    return dc_gain


def suggest_stable_parameters(target_temp=25.0, input_flow=0.6):
    """
    Suggest stable parameters for reasonable greenhouse control.

    Goal: Reach ~25C with Flow=0.6, stable response
    """
    print("\n" + "=" * 70)
    print("SUGGESTED STABLE PARAMETERS")
    print("=" * 70)

    # Target: K * Flow = target_temp
    # So K = target_temp / Flow
    K_suggested = target_temp / input_flow

    print(f"\nFor target temperature {target_temp}C with Flow={input_flow}:")
    print(f"  Suggested K = {K_suggested:.2f}")
    print(f"  Suggested T1 = 120 s (keep original)")
    print(f"  Suggested T2 = 60 s (keep original)")
    print(f"  Suggested L = 10 s (keep original)")

    print(f"\nOr for faster response:")
    print(f"  K = {K_suggested:.2f}")
    print(f"  T1 = 60 s")
    print(f"  T2 = 30 s")
    print(f"  L = 5 s")

    print(f"\nOr for very stable (slow) response:")
    print(f"  K = {K_suggested/2:.2f}  <- Lower gain")
    print(f"  T1 = 240 s")
    print(f"  T2 = 120 s")
    print(f"  L = 10 s")

    print("\n" + "=" * 70)

    return {'K': K_suggested, 'T1': 120.0, 'T2': 60.0, 'L': 10.0}


if __name__ == '__main__':
    # Test with current default parameters
    print("Analyzing CURRENT (problematic) parameters:\n")
    params_bad = ModelParams(K=0.8, T1=120.0, T2=60.0, L=10.0)
    dc_gain = analyze_stability(params_bad)

    # Suggest better parameters
    suggested = suggest_stable_parameters(target_temp=25.0, input_flow=0.6)

    print("\n\nAnalyzing SUGGESTED (stable) parameters:\n")
    params_good = ModelParams(**suggested)
    analyze_stability(params_good)

    print("\n\n[PLOT] Generating plots...")
    print("  (Close plot windows to continue)")

    # Plot step response
    fig1 = plot_step_response(params_bad, duration=600)
    fig1.suptitle('CURRENT Parameters (K=0.8) - PROBLEMATIC', fontsize=16, fontweight='bold', color='red')

    fig2 = plot_step_response(params_good, duration=600)
    fig2.suptitle('SUGGESTED Parameters - STABLE', fontsize=16, fontweight='bold', color='green')

    # Plot Bode
    fig3 = plot_bode(params_bad)
    fig3.suptitle('CURRENT Parameters - Frequency Response', fontsize=16, fontweight='bold')

    fig4 = plot_bode(params_good)
    fig4.suptitle('SUGGESTED Parameters - Frequency Response', fontsize=16, fontweight='bold')

    # Plot Nyquist
    fig5 = plot_nyquist(params_bad)
    fig5.suptitle('CURRENT Parameters - Nyquist', fontsize=16, fontweight='bold')

    fig6 = plot_nyquist(params_good)
    fig6.suptitle('SUGGESTED Parameters - Nyquist', fontsize=16, fontweight='bold')

    plt.show()

    print("\n[OK] Analysis complete!")
