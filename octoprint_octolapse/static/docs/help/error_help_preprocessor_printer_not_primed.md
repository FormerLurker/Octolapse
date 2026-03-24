Priming could not be detected.  The will prevent Octolapse from taking any snapshots.

#### Steps to solve

1.  If there are any other errors reported, fix those first.  This problem is usually caused by axis mode detection problems.
2.  Open your printer profile settings and find the  **Priming Height** within the **Layer Change Detection** setting.  This should be set to the height at which your printer primes.  Many printers prime at 5MM, but some (like mine) prime at about 0.3MM directly on the bed.  If your printer primes above your print bed, this setting is critical.  If in doubt, set this value to your current layer height (0.2 is common), or set to 0 to disable priming detection.  **Warning**: if priming detection is disabled or incorrect, Octolapse may take a snapshot while priming, then will fail to capture more snapshots until the priming height is reached.
