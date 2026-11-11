"""
Assemble les slides verticales (1080x1920) d'un carrousel en une vidéo Reel MP4.

Utilisation :
    python3 generer.py faune_extreme/AAAA-MM-JJ.json --reel      -> sortie/AAAA-MM-JJ_reel/slide_0N.png
    python3 faire_reel.py sortie/AAAA-MM-JJ_reel reel.mp4

Durées : couverture 4 s, chaque fait 9 s (le temps de lire tranquillement), slide finale 5 s ; léger zoom et transition glissée.
Nécessite ffmpeg.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

FONDU = 0.5


def main():
    dossier, sortie = Path(sys.argv[1]), Path(sys.argv[2])
    slides = sorted(dossier.glob("slide_*.png"))
    durees = [4] + [9] * (len(slides) - 2) + [5]
    with tempfile.TemporaryDirectory() as tmp:
        clips = []
        for i, (img, d) in enumerate(zip(slides, durees)):
            clip = Path(tmp) / f"c{i}.mp4"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(d),
                            "-i", str(img), "-vf",
                            "scale=1080:1920,zoompan=z='1+0.0005*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            ":d=1:s=1080x1920:fps=30,format=yuv420p",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(clip)], check=True)
            clips.append(clip)
        entrees, filtres, prec, t = [], [], "[0]", 0.0
        for c in clips:
            entrees += ["-i", str(c)]
        for i in range(1, len(clips)):
            t += durees[i - 1] - FONDU
            sortie_f = f"[v{i}]"
            filtres.append(f"{prec}[{i}]xfade=transition=slideleft:duration={FONDU}:offset={t:.2f}{sortie_f}")
            prec = sortie_f
        filtres[-1] = filtres[-1].replace(prec, ",format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *entrees, "-filter_complex", ";".join(filtres),
                        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-movflags", "+faststart", str(sortie)], check=True)
    print("✓", sortie)


if __name__ == "__main__":
    main()
