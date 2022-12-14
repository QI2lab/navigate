import numpy as np
import numpy.typing as npt

# Mostly follows Lin R, Clowsley AH, Jayasinghe ID, Baddeley D, Soeller C. 
# Algorithmic corrections for localization microscopy with sCMOS cameras -
# characterisation of a computationally efficient localization approach. 
# Optics Express. 2017;25(10):11701–11701. 

def compute_scmos_offset_and_variance_map(image: npt.ArrayLike) \
    -> tuple[npt.ArrayLike, npt.ArrayLike]:
    """ Compute the offset and variance map of an sCMOS camera.
    
    Parameters
    ----------
    image : npt.ArrayLike
        ZYX image of multiple dark camera frames, taken sequentially.
    """
    offset_map = np.mean(image, axis=0)
    variance_map = np.var(image, axis=0)

    return offset_map, variance_map

def compute_flatfield_map(image: np.ArrayLike, offset_map: np.ArrayLike, 
                           local: bool = False) -> npt.ArrayLike:
    """Compute the flatfield map for our system.
    
    Parameters
    ----------
    image : npt.ArrayLike
        ZYX image of multiple camera frames with defocused, even signal.
    offset_map : np.ArrayLike
        XY image of camera offset in the absence of signal.
    local : bool
        Compute the local flatfield map (as opposed to global).
    """
    offset_image = np.mean(image, axis=0) - offset_map
    if local:
        from scipy.ndimage import gaussian_filter
        
        gaussian_image = gaussian_filter(offset_image, 9)
        return offset_image/(gaussian_image + 1)
    else:
        return offset_image/(np.max(np.abs(offset_image)) + 1)

def compute_noise_sigma(Fn=1.0, qe=0.82, S=0.0, Ib=100.0, Nr=1.4, M=1.0):
    """
    Using https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/sys/SCAS0134E_C13440-20CU_tec.pdf
    the noise sigma is given by

    Parameters
    ----------
    Fn : float
        Excess noise factor (unitless)
    qe : float
        Quantum efficiency (unitless)
    S : float or np.array
        Signal (photons/pixel/frame)
    Ib : float or np.array
        Background (photons/pixel/frame)
    Nr : float
        Readout noise (e- rms)
    M : float
        EM Gain

    Returns
    --------
    noise : float or np.array
        Estimated noise model
    """
    noise = np.sqrt(Fn*Fn*qe*(S+Ib)+(Nr/M)**2)
    return noise

def compute_signal_to_noise(Fn=1.0, qe=0.82, S=0.0, Ib=100.0, Nr=1.4, M=1.0, offset_map=None):
    """https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/sys/SCAS0134E_C13440-20CU_tec.pdf"""
    if offset_map is not None and S.shape == offset_map.shape:
        S -= offset_map
        Ib = 0.0
    sig = compute_noise_sigma(Fn=Fn, qe=qe, S=S, Ib=Ib, Nr=Nr, M=M)
    return qe*S/sig
