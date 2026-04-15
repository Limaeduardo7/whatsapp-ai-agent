import {Composition} from 'remotion';
import {Video} from './video';

export const Root = () => {
  return (
    <>
      <Composition
        id="V8Pixel"
        component={Video}
        durationInFrames={360}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
