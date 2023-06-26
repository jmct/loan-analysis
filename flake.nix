{
  description = "Planes!";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        inherit system;
      };
      python-with-my-packages = pkgs.python3.withPackages(ps: with ps; [
            pandas
            pip
            virtualenv
          ]);
    in rec {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          python-with-my-packages
          libsodium
          pandoc
          texlive.combined.scheme-small
        ];
        nativeBuildInputs = [pkgs.autoPatchelfHook ];        
        shellHook = "
          export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib
          python -m venv .venv
          source .venv/bin/activate
          python -m pip install -r requirements.txt
          export PYTHONPATH=$(pwd)/.venv/python3.10/site-packages:${python-with-my-packages}/${python-with-my-packages.sitePackages}
          ipython kernel install --user --name=venv
          ";
      };
    }
  );

}
