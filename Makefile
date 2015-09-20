all: linux wine

linux:
	pyinstaller --clean --noconfirm padpyght-bin.spec
	cd dist; tar czf padpyght-linux.tar.gz padpyght-bin

wine:
	wine pyinstaller --clean --noconfirm padpyght-bin.spec
	cd dist; zip -r padpyght-win32.zip padpyght-bin

clean:
	rm -rf build/ dist/
