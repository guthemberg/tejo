filename=main
final_version=report.pdf

pdf:
	pdflatex ${filename}
	bibtex ${filename}||true
	pdflatex ${filename}
	pdflatex ${filename}
	cp ${filename}.pdf ${final_version}

clean:
	rm -f ${final_version} ${filename}.ps ${filename}.pdf ${filename}.log ${filename}.aux ${filename}.out ${filename}.dvi ${filename}.bbl main.synctex.gz ${filename}.blg ${filename}.toc ${filename}.lof ${filename}.lot
