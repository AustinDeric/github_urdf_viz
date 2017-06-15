import deploy

owner = 'ros-industrial'
repo = 'abb_experimental'
branch = 'irb52_mention_variants'
package = ' abb_irb52_support'
launch_file = 'load_irb52_7_145.launch'

# docker stuff
deploy.local_build(cmd=cmd)
